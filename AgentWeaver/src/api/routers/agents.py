
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from src.api.models import (
    AgentResponse, 
    AgentListResponse, 
    AgentRegistrationRequest,
    AgentUpdateRequest,
    AgentStatus,
    ErrorResponse
)
from src.orchestration.supervisor import SupervisorNode

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agents", tags=["Agents"])


def get_supervisor() -> SupervisorNode:
    # This will be injected from the main app state
    from main import app
    return app.state.supervisor


def convert_agent_to_response(agent_data: Dict[str, Any]) -> AgentResponse:
    try:
        # Extract agent information from the supervisor data structure
        agent_id = agent_data.get("id", "unknown")
        agent_name = agent_data.get("name", f"Agent {agent_id}")
        agent_type = agent_data.get("type", "unknown")
        
        # Map internal status to API status enum
        internal_status = agent_data.get("status", "unknown")
        status_mapping = {
            "available": AgentStatus.IDLE,
            "busy": AgentStatus.BUSY,
            "error": AgentStatus.ERROR,
            "active": AgentStatus.ACTIVE,
            "offline": AgentStatus.OFFLINE
        }
        status = status_mapping.get(internal_status, AgentStatus.IDLE)
        
        # Extract capabilities
        capabilities = agent_data.get("capabilities", [])
        if isinstance(capabilities, str):
            capabilities = [capabilities]
        
        # Extract performance metrics
        performance_metrics = agent_data.get("performance_metrics", {})
        if not isinstance(performance_metrics, dict):
            performance_metrics = {}
        
        # Extract metadata
        metadata = agent_data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        
        return AgentResponse(
            id=agent_id,
            name=agent_name,
            type=agent_type,
            status=status,
            capabilities=capabilities,
            current_task=agent_data.get("current_task"),
            last_activity=metadata.get("last_activity"),
            performance_metrics=performance_metrics,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error converting agent data to response: {e}")
        # Return a basic response with minimal data
        return AgentResponse(
            id=agent_data.get("id", "unknown"),
            name=agent_data.get("name", "Unknown Agent"),
            type=agent_data.get("type", "unknown"),
            status=AgentStatus.ERROR,
            capabilities=[],
            performance_metrics={},
            metadata={"conversion_error": str(e)}
        )


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    status: Optional[str] = Query(None, description="Filter agents by status"),
    agent_type: Optional[str] = Query(None, description="Filter agents by type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of agents to return"),
    offset: int = Query(0, ge=0, description="Number of agents to skip"),
    supervisor: SupervisorNode = Depends(get_supervisor)
):
    try:
        logger.info(f"Listing agents with filters - status: {status}, type: {agent_type}")
        
        # Get agent registry from supervisor
        # For now, we'll create mock data since the supervisor integration is not complete
        mock_agents = [
            {
                "id": "text_analyst_001",
                "name": "Senior Text Analyst",
                "type": "text_analysis",
                "status": "active",
                "capabilities": ["sentiment_analysis", "entity_extraction", "topic_classification"],
                "current_task": None,
                "performance_metrics": {
                    "tasks_completed": 45,
                    "avg_processing_time": 2.3,
                    "success_rate": 0.96
                },
                "metadata": {
                    "version": "1.0",
                    "last_activity": "2025-08-02T14:20:00Z"
                }
            },
            {
                "id": "data_processor_001", 
                "name": "Data Processing Specialist",
                "type": "data_processing",
                "status": "busy",
                "capabilities": ["data_cleaning", "aggregation", "transformation"],
                "current_task": "workflow_001",
                "performance_metrics": {
                    "tasks_completed": 32,
                    "avg_processing_time": 4.1,
                    "success_rate": 0.91
                },
                "metadata": {
                    "version": "1.2",
                    "last_activity": "2025-08-02T14:22:00Z"
                }
            },
            {
                "id": "api_specialist_001",
                "name": "API Integration Agent",
                "type": "api_interaction", 
                "status": "idle",
                "capabilities": ["rest_api", "graphql", "webhook_handling"],
                "current_task": None,
                "performance_metrics": {
                    "tasks_completed": 28,
                    "avg_processing_time": 1.8,
                    "success_rate": 0.94
                },
                "metadata": {
                    "version": "1.1",
                    "last_activity": "2025-08-02T14:15:00Z"
                }
            }
        ]
        
        # Apply filters
        filtered_agents = mock_agents
        
        if status:
            filtered_agents = [a for a in filtered_agents if a.get("status") == status]
        
        if agent_type:
            filtered_agents = [a for a in filtered_agents if a.get("type") == agent_type]
        
        # Apply pagination
        total_count = len(filtered_agents)
        paginated_agents = filtered_agents[offset:offset + limit]
        
        # Convert to response format
        agent_responses = [convert_agent_to_response(agent) for agent in paginated_agents]
        
        # Calculate counts
        active_count = sum(1 for a in filtered_agents if a.get("status") == "active")
        busy_count = sum(1 for a in filtered_agents if a.get("status") == "busy")
        
        response = AgentListResponse(
            agents=agent_responses,
            total_count=total_count,
            active_count=active_count,
            busy_count=busy_count,
            metadata={
                "last_updated": datetime.now().isoformat(),
                "filters_applied": {
                    "status": status,
                    "type": agent_type
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset
                }
            }
        )
        
        logger.info(f"Successfully listed {len(agent_responses)} agents")
        return response
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agents: {str(e)}"
        )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_details(
    agent_id: str,
    supervisor: SupervisorNode = Depends(get_supervisor)
):
    try:
        logger.info(f"Getting details for agent: {agent_id}")
        
        # Mock agent data for demonstration
        # In a real implementation, this would query the supervisor's agent registry
        mock_agents = {
            "text_analyst_001": {
                "id": "text_analyst_001",
                "name": "Senior Text Analyst",
                "type": "text_analysis",
                "status": "active",
                "capabilities": ["sentiment_analysis", "entity_extraction", "topic_classification", "language_detection"],
                "current_task": None,
                "performance_metrics": {
                    "tasks_completed": 45,
                    "avg_processing_time": 2.3,
                    "success_rate": 0.96,
                    "total_runtime": 1847.5,
                    "peak_memory_usage": 256.7
                },
                "metadata": {
                    "version": "1.0",
                    "created_at": "2025-08-01T10:00:00Z",
                    "last_activity": "2025-08-02T14:20:00Z",
                    "configuration": {
                        "max_text_length": 10000,
                        "confidence_threshold": 0.85,
                        "model_version": "v2.1"
                    },
                    "tags": ["nlp", "production", "high-accuracy"]
                }
            },
            "data_processor_001": {
                "id": "data_processor_001",
                "name": "Data Processing Specialist", 
                "type": "data_processing",
                "status": "busy",
                "capabilities": ["data_cleaning", "aggregation", "transformation", "validation"],
                "current_task": "workflow_001",
                "performance_metrics": {
                    "tasks_completed": 32,
                    "avg_processing_time": 4.1,
                    "success_rate": 0.91,
                    "total_runtime": 2156.3,
                    "peak_memory_usage": 512.1
                },
                "metadata": {
                    "version": "1.2",
                    "created_at": "2025-08-01T10:05:00Z",
                    "last_activity": "2025-08-02T14:22:00Z",
                    "configuration": {
                        "batch_size": 1000,
                        "timeout": 300,
                        "retry_attempts": 3
                    },
                    "tags": ["data", "production", "batch-processing"]
                }
            },
            "api_specialist_001": {
                "id": "api_specialist_001",
                "name": "API Integration Agent",
                "type": "api_interaction",
                "status": "idle", 
                "capabilities": ["rest_api", "graphql", "webhook_handling", "authentication"],
                "current_task": None,
                "performance_metrics": {
                    "tasks_completed": 28,
                    "avg_processing_time": 1.8,
                    "success_rate": 0.94,
                    "total_runtime": 892.4,
                    "peak_memory_usage": 128.3
                },
                "metadata": {
                    "version": "1.1",
                    "created_at": "2025-08-01T10:10:00Z", 
                    "last_activity": "2025-08-02T14:15:00Z",
                    "configuration": {
                        "timeout": 30,
                        "max_retries": 5,
                        "rate_limit": 100
                    },
                    "tags": ["api", "production", "integration"]
                }
            }
        }
        
        # Check if agent exists
        if agent_id not in mock_agents:
            logger.warning(f"Agent not found: {agent_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_id}' not found"
            )
        
        agent_data = mock_agents[agent_id]
        response = convert_agent_to_response(agent_data)
        
        logger.info(f"Successfully retrieved details for agent: {agent_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting agent details for {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agent details: {str(e)}"
        )


@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str):
    try:
        # Mock status data
        status_data = {
            "agent_id": agent_id,
            "status": "active",
            "current_task": None,
            "last_heartbeat": datetime.now().isoformat(),
            "uptime": 3600.5,
            "resource_usage": {
                "cpu_percent": 15.2,
                "memory_percent": 23.8
            }
        }
        
        return status_data
        
    except Exception as e:
        logger.error(f"Error getting agent status for {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agent status: {str(e)}"
        )


@router.get("/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    try:
        # Mock metrics data
        metrics_data = {
            "agent_id": agent_id,
            "performance_metrics": {
                "tasks_completed_today": 15,
                "tasks_completed_total": 45,
                "avg_processing_time": 2.3,
                "success_rate": 0.96,
                "error_rate": 0.04,
                "throughput_per_hour": 12.5
            },
            "resource_metrics": {
                "current_cpu_usage": 15.2,
                "peak_cpu_usage": 78.9,
                "current_memory_usage": 256.7,
                "peak_memory_usage": 412.3
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics_data
        
    except Exception as e:
        logger.error(f"Error getting agent metrics for {agent_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agent metrics: {str(e)}"
        )
