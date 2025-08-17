"""
Agriculture API Router
Provides REST API endpoints for agricultural queries and agent management.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ...core.agriculture_models import (
    AgricultureQuery, QueryDomain, Language, Location, FarmProfile
)
from ...services.agriculture_integration import get_agriculture_service
from src.agents.harvest_planning_agent import HarvestPlanningAgent
from src.core.agriculture_models import AgricultureQuery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agriculture", tags=["Agriculture"])


# Request/Response Models
class AgricultureQueryRequest(BaseModel):
    """Request model for agricultural queries"""
    query_text: str = Field(..., description="The agricultural question or query")
    user_id: Optional[str] = Field(None, description="User identifier")
    language: Language = Field(Language.ENGLISH, description="Query language")
    location: Optional[Dict[str, Any]] = Field(None, description="User location information")
    farm_profile: Optional[Dict[str, Any]] = Field(None, description="Farm profile data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    priority: str = Field("medium", description="Query priority (low, medium, high)")


class AgricultureQueryResponse(BaseModel):
    """Response model for agricultural queries"""
    status: str
    query_id: str
    message: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    estimated_time: Optional[int] = None  # seconds


class AgricultureStatusResponse(BaseModel):
    """Response model for agriculture system status"""
    status: str
    router_available: bool
    specialist_agents: int
    active_queries: int
    agent_details: Dict[str, Any] = Field(default_factory=dict)


@router.post("/query", response_model=AgricultureQueryResponse)
async def submit_agriculture_query(
    request: AgricultureQueryRequest,
    background_tasks: BackgroundTasks
) -> AgricultureQueryResponse:
    """
    Submit an agricultural query for processing.
    The query will be analyzed and routed to appropriate specialist agents.
    """
    try:
        # Get agriculture service
        service = get_agriculture_service()
        if not service:
            raise HTTPException(
                status_code=503, 
                detail="Agriculture service not available"
            )
        
        # Convert request to AgricultureQuery
        query_data = {
            "query_text": request.query_text,
            "user_id": request.user_id,
            "query_language": request.language,
            "context": request.context,
            "priority": request.priority
        }
        
        # Add location if provided
        if request.location:
            query_data["location"] = Location(**request.location)
        
        # Add farm profile if provided
        if request.farm_profile:
            query_data["farm_profile"] = FarmProfile(**request.farm_profile)
        
        logger.info(f"Received agriculture query: {request.query_text[:100]}...")
        
        # Process query (this will be async and send updates via WebSocket)
        result = await service.handle_agriculture_query(query_data)
        
        if "error" in result:
            return AgricultureQueryResponse(
                status="error",
                query_id="",
                error=result["error"]
            )
        
        elif result.get("status") == "clarification_needed":
            return AgricultureQueryResponse(
                status="clarification_needed",
                query_id=result["query_id"],
                message="Need more information",
                response={"questions": result["questions"]}
            )
        
        else:
            return AgricultureQueryResponse(
                status="success",
                query_id=result["query_id"],
                message="Query processed successfully",
                response=result["response"]
            )
    
    except Exception as e:
        logger.error(f"Failed to process agriculture query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=AgricultureStatusResponse)
async def get_agriculture_status() -> AgricultureStatusResponse:
    """
    Get the current status of the agriculture system.
    Shows availability of router, specialist agents, and active queries.
    """
    try:
        service = get_agriculture_service()
        if not service:
            return AgricultureStatusResponse(
                status="unavailable",
                router_available=False,
                specialist_agents=0,
                active_queries=0
            )
        
        status_data = await service.get_status({})
        
        return AgricultureStatusResponse(
            status=status_data.get("status", "unknown"),
            router_available=status_data.get("router_available", False),
            specialist_agents=status_data.get("specialist_agents", 0),
            active_queries=status_data.get("active_queries", 0),
            agent_details=status_data.get("agent_details", {})
        )
    
    except Exception as e:
        logger.error(f"Failed to get agriculture status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/{query_id}")
async def get_query_status(query_id: str) -> Dict[str, Any]:
    """
    Get the status of a specific query by ID.
    Shows processing status, responses, and completion status.
    """
    try:
        service = get_agriculture_service()
        if not service:
            raise HTTPException(
                status_code=503, 
                detail="Agriculture service not available"
            )
        
        query_status = service.get_query_status(query_id)
        
        if not query_status:
            raise HTTPException(
                status_code=404, 
                detail=f"Query {query_id} not found"
            )
        
        # Convert datetime objects to strings for JSON serialization
        response_data = {
            "query_id": query_id,
            "status": query_status["status"],
            "start_time": query_status["start_time"].isoformat(),
            "responses_count": len(query_status.get("responses", {}))
        }
        
        # Add final response if completed
        if "final_response" in query_status:
            response_data["final_response"] = query_status["final_response"].dict()
        
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains")
async def get_supported_domains() -> Dict[str, Any]:
    """
    Get list of supported agricultural domains and their descriptions.
    """
    try:
        domains_info = {
            QueryDomain.CROP_SELECTION.value: {
                "name": "Crop Selection",
                "description": "Recommendations for optimal crop varieties based on location, soil, and weather conditions",
                "keywords": ["crop", "seed", "variety", "plant", "cultivation", "fasal", "beej"]
            },
            QueryDomain.PEST_MANAGEMENT.value: {
                "name": "Pest Management", 
                "description": "Pest identification, outbreak forecasting, and treatment recommendations",
                "keywords": ["pest", "insect", "disease", "spray", "treatment", "keet", "bimari"]
            },
            QueryDomain.IRRIGATION.value: {
                "name": "Irrigation Scheduling",
                "description": "Water requirement calculation and optimal irrigation scheduling",
                "keywords": ["water", "irrigation", "watering", "schedule", "pani", "sinchai"]
            },
            QueryDomain.FINANCE_POLICY.value: {
                "name": "Finance & Policy",
                "description": "Agricultural loans, subsidies, insurance, and government schemes",
                "keywords": ["loan", "subsidy", "insurance", "scheme", "bank", "karza", "yojana"]
            },
            QueryDomain.MARKET_TIMING.value: {
                "name": "Market Timing",
                "description": "Price forecasting and optimal selling time recommendations",
                "keywords": ["sell", "market", "price", "mandi", "rate", "bhav"]
            },
            QueryDomain.HARVEST_PLANNING.value: {
                "name": "Harvest Planning",
                "description": "Optimal harvest timing and post-harvest handling advice",
                "keywords": ["harvest", "cutting", "maturity", "katana", "fasal"]
            },
            QueryDomain.INPUT_MATERIALS.value: {
                "name": "Input Materials",
                "description": "Fertilizer, seed, and pesticide recommendations with cost optimization",
                "keywords": ["fertilizer", "seed", "pesticide", "khad", "urvarak", "beej"]
            }
        }
        
        return {
            "supported_domains": domains_info,
            "languages": {
                Language.ENGLISH.value: "English",
                Language.HINDI.value: "Hindi (हिंदी)",
                Language.MIXED.value: "Mixed (Hindi-English)"
            },
            "example_queries": [
                {
                    "domain": QueryDomain.CROP_SELECTION.value,
                    "query": "What crop should I grow in Punjab during Rabi season?",
                    "hindi": "रबी के मौसम में पंजाब में कौन सी फसल उगानी चाहिए?"
                },
                {
                    "domain": QueryDomain.PEST_MANAGEMENT.value,
                    "query": "My wheat has yellow spots, what spray should I use?",
                    "hindi": "मेरे गेहूं पर पीले धब्बे हैं, कौन सा स्प्रे करूं?"
                },
                {
                    "domain": QueryDomain.IRRIGATION.value,
                    "query": "When should I water my cotton crop?",
                    "hindi": "कपास की फसल में कब पानी देना चाहिए?"
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to get supported domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit feedback on agricultural advice quality.
    Used to improve agent responses and accuracy.
    """
    try:
        # Log feedback for analysis
        logger.info(f"Received agriculture feedback: {feedback_data}")
        
        # In a production system, this would be stored in a database
        # For now, we'll just acknowledge receipt
        
        return {
            "status": "success",
            "message": "Thank you for your feedback!",
            "feedback_id": f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_agriculture_system() -> Dict[str, Any]:
    """
    Test endpoint to verify agriculture system is working.
    Runs basic connectivity and functionality tests.
    """
    try:
        service = get_agriculture_service()
        
        tests = {
            "service_available": service is not None,
            "router_initialized": False,
            "agents_registered": 0
        }
        
        if service:
            status = await service.get_status({})
            tests["router_initialized"] = status.get("router_available", False)
            tests["agents_registered"] = status.get("specialist_agents", 0)
        
        overall_status = "healthy" if all([
            tests["service_available"],
            tests["router_initialized"]
        ]) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "tests": tests,
            "message": "Agriculture system test completed"
        }
    
    except Exception as e:
        logger.error(f"Agriculture system test failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Agriculture system test failed"
        }
# Initialize the harvest planning agent
harvest_agent = HarvestPlanningAgent()

@router.post("/query")
async def process_agriculture_query(query: AgricultureQuery):
    """Process agriculture query and return agent response"""
    try:
        logger.info(f"Processing query: {query.query_text}")
        
        # Process query with harvest planning agent
        response = await harvest_agent.process_query(query)
        
        return {
            "status": "success",
            "query_id": query.query_id,
            "response": {
                "agent_name": response.agent_name,
                "response_text": response.response_text,
                "confidence_score": response.confidence_score,
                "recommendations": response.recommendations,
                "reasoning": response.reasoning,
                "sources": response.sources if hasattr(response, 'sources') else [],
                "next_steps": response.next_steps if hasattr(response, 'next_steps') else [],
                "metadata": response.metadata if hasattr(response, 'metadata') else {}
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing agriculture query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@router.get("/agents/harvest")
async def get_harvest_agent_status():
    """Get harvest planning agent status"""
    return {
        "agent_id": "harvest_planning_agent",
        "name": "Harvest Planning Agent",
        "status": "active",
        "capabilities": ["harvest_timing", "crop_calendar", "weather_analysis"]
    }