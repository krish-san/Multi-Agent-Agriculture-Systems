"""
Demo API Router
Provides endpoints to access the multi-agent agriculture demo functionality
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Import demo system
try:
    from demo_presentation import AgricultureDemoSystem
except ImportError:
    # Create a fallback demo system if the main one isn't available
    class AgricultureDemoSystem:
        def __init__(self):
            self.session_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.demo_queries = []
            self.mock_satellite_data = {
                "punjab_ludhiana": {
                    "ndvi": 0.72,
                    "soil_moisture": 0.45,
                    "temperature": 28.5,
                    "humidity": 65,
                    "environmental_score": 78,
                    "risk_level": "moderate"
                },
                "maharashtra_nagpur": {
                    "ndvi": 0.58,
                    "soil_moisture": 0.25,
                    "temperature": 35.2,
                    "humidity": 45,
                    "environmental_score": 62,
                    "risk_level": "high"
                }
            }
        
        def _simulate_agent_routing(self, query: str):
            routing_map = {
                "गेहूं": "crop_selection",
                "wheat": "crop_selection", 
                "पत्ते": "pest_management",
                "pest": "pest_management",
                "sell": "market_timing",
                "profit": "market_timing",
                "irrigation": "irrigation",
                "water": "irrigation",
                "loan": "finance_policy",
                "apply": "finance_policy"
            }
            
            query_lower = query.lower()
            for keyword, agent in routing_map.items():
                if keyword in query_lower:
                    return {
                        "agent": agent,
                        "confidence": 0.92,
                        "reasoning": f"Detected '{keyword}' indicating {agent} domain",
                        "language_detected": self._detect_language(query)
                    }
            
            return {
                "agent": "general_agriculture", 
                "confidence": 0.75,
                "reasoning": "General agricultural query",
                "language_detected": self._detect_language(query)
            }
        
        def _detect_language(self, query: str):
            hindi_chars = any('\u0900' <= char <= '\u097F' for char in query)
            english_chars = any('a' <= char.lower() <= 'z' for char in query)
            
            if hindi_chars and english_chars:
                return "mixed"
            elif hindi_chars:
                return "hindi"
            else:
                return "english"
        
        def _generate_satellite_enhanced_response(self, query_info, routing):
            agent = routing["agent"]
            language = routing["language_detected"]
            location_key = "punjab_ludhiana"
            satellite_data = self.mock_satellite_data[location_key]
            
            # Generate appropriate response based on agent and language
            if agent == "crop_selection":
                if language in ["hindi", "mixed"]:
                    return f"""🌾 नमस्ते किसान भाई! पंजाब में गेहूं की बेहतरीन किस्में:

**🛰️ उपग्रह डेटा विश्लेषण:**
• NDVI स्कोर: {satellite_data['ndvi']} (अच्छी मिट्टी की स्थिति)
• मिट्टी में नमी: {satellite_data['soil_moisture']*100:.0f}%
• पर्यावरणीय स्कोर: {satellite_data['environmental_score']}/100

**सुझावी किस्में:**
1. **HD-2967**: उच्च उत्पादन (45-50 क्विंटल/एकड़)
2. **PBW-343**: रोग प्रतिरोधी, सिंचाई वाले क्षेत्रों के लिए
3. **DBW-88**: देर से बुआई के लिए उत्तम

**🛰️ उपग्रह सिफारिश:** मौजूदा मिट्टी की स्थिति के अनुसार HD-2967 सबसे उपयुक्त है।
**विश्वसनीयता:** 95% ✅"""
                else:
                    return f"""🌾 Hello Farmer! Best wheat varieties for Punjab:

**🛰️ Satellite Analysis:**
• NDVI Score: {satellite_data['ndvi']} (Good field conditions)
• Soil Moisture: {satellite_data['soil_moisture']*100:.0f}%
• Environmental Score: {satellite_data['environmental_score']}/100

**Recommended Varieties:**
1. **HD-2967**: High yield (45-50 quintals/acre)
2. **PBW-343**: Disease resistant, ideal for irrigated areas
3. **DBW-88**: Perfect for late sowing

**🛰️ Satellite Recommendation:** Based on current soil conditions, HD-2967 is most suitable.
**Confidence:** 95% ✅"""
            elif agent == "pest_management":
                return f"""🐛 Pest Management Analysis:

**🛰️ Field Health Status:**
• NDVI: {satellite_data['ndvi']} (Field condition indicator)
• Temperature: {satellite_data['temperature']}°C
• Humidity: {satellite_data['humidity']}%

**Diagnosis:** Yellow leaves + environmental conditions = **Possible fungal infection**

**Recommended Action:**
1. Apply copper-based fungicide
2. Improve field drainage
3. Use neem oil + soap solution

**🛰️ Satellite Monitoring:** Risk level: {satellite_data['risk_level'].upper()}
**Success Rate:** 88% with early treatment ✅"""
            else:
                return f"""🌾 Agricultural Advisory:

**🛰️ Current Field Analysis:**
• Environmental Score: {satellite_data['environmental_score']}/100
• Risk Level: {satellite_data['risk_level'].upper()}
• Field Health: Good (NDVI: {satellite_data['ndvi']})

**Recommendation:** Based on satellite data analysis, your field is in {satellite_data['risk_level']} condition.
**Confidence:** 90% ✅"""

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/demo", tags=["Demo"])

# Global demo system instance
demo_system = None

def get_demo_system():
    """Get or create demo system instance"""
    global demo_system
    if demo_system is None:
        demo_system = AgricultureDemoSystem()
    return demo_system


# Request/Response Models
class DemoQueryRequest(BaseModel):
    """Request model for demo queries"""
    query_text: str = Field(..., description="The agricultural question to ask")
    language: Optional[str] = Field(None, description="Preferred language (hindi/english/mixed)")
    location: Optional[str] = Field("punjab_ludhiana", description="Location for satellite data")


class DemoQueryResponse(BaseModel):
    """Response model for demo queries"""
    status: str
    query_id: str
    original_query: str
    routing_analysis: Dict[str, Any]
    satellite_data: Dict[str, Any]
    response_text: str
    technical_metrics: Dict[str, Any]
    timestamp: str


class DemoCapabilitiesResponse(BaseModel):
    """Response model for demo capabilities"""
    system_status: str
    completion_percentage: int
    operational_agents: List[str]
    capabilities: List[str]
    satellite_features: List[str]
    supported_languages: List[str]


class DemoSessionResponse(BaseModel):
    """Response model for demo session info"""
    session_id: str
    start_time: str
    total_queries: int
    sample_queries: List[Dict[str, str]]


@router.get("/capabilities", response_model=DemoCapabilitiesResponse)
async def get_demo_capabilities():
    """Get overview of demo system capabilities"""
    try:
        demo = get_demo_system()
        
        return DemoCapabilitiesResponse(
            system_status="Satellite-Enhanced AI Agricultural Advisory System",
            completion_percentage=71,
            operational_agents=[
                "crop_selection", "pest_management", "irrigation", 
                "finance_policy", "market_timing"
            ],
            capabilities=[
                "Multilingual Query Processing (Hindi/English/Mixed)",
                "Intelligent Agent Routing",
                "Satellite Data Integration", 
                "Real-time Agricultural Advisory",
                "Confidence-based Recommendations"
            ],
            satellite_features=[
                "NDVI Analysis", "Soil Moisture Monitoring",
                "Weather Prediction", "Risk Assessment",
                "Environmental Scoring"
            ],
            supported_languages=["hindi", "english", "mixed"]
        )
    except Exception as e:
        logger.error(f"Error getting demo capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session", response_model=DemoSessionResponse)
async def get_demo_session():
    """Get current demo session information"""
    try:
        demo = get_demo_system()
        
        sample_queries = [
            {
                "query": "पंजाब में गेहूं की सबसे अच्छी किस्म कौन सी है?",
                "type": "Hindi crop selection",
                "agent": "crop_selection"
            },
            {
                "query": "Meri cotton crop mein पीले पत्ते दिख रहे हैं, क्या करूं?",
                "type": "Code-switched pest management",
                "agent": "pest_management"
            },
            {
                "query": "When should I sell my wheat crop for maximum profit?",
                "type": "English market timing",
                "agent": "market_timing"
            },
            {
                "query": "My field needs irrigation - when and how much water?",
                "type": "Irrigation scheduling",
                "agent": "irrigation"
            },
            {
                "query": "Loan ke liye apply कैसे करूं for farming equipment?",
                "type": "Financial advisory",
                "agent": "finance_policy"
            }
        ]
        
        return DemoSessionResponse(
            session_id=demo.session_id,
            start_time=datetime.now().isoformat(),
            total_queries=len(sample_queries),
            sample_queries=sample_queries
        )
    except Exception as e:
        logger.error(f"Error getting demo session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=DemoQueryResponse)
async def process_demo_query(request: DemoQueryRequest):
    """Process a demo agricultural query with satellite enhancement"""
    try:
        demo = get_demo_system()
        
        # Process the query using demo system
        start_time = datetime.now()
        
        # Simulate agent routing
        routing = demo._simulate_agent_routing(request.query_text)
        
        # Get satellite data
        location_key = request.location or "punjab_ludhiana"
        if location_key not in demo.mock_satellite_data:
            location_key = "punjab_ludhiana"  # fallback
        
        satellite_data = demo.mock_satellite_data[location_key]
        
        # Generate response
        query_info = {
            "text": request.query_text,
            "language": request.language or routing["language_detected"]
        }
        
        response_data = demo._generate_satellite_enhanced_response(query_info, routing)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create unique query ID
        query_id = f"demo_query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        technical_metrics = {
            "processing_time_ms": round(processing_time, 0),
            "confidence_level": routing["confidence"],
            "satellite_data_integrated": True,
            "risk_assessment": satellite_data["risk_level"].upper(),
            "agent": routing["agent"]
        }
        
        return DemoQueryResponse(
            status="success",
            query_id=query_id,
            original_query=request.query_text,
            routing_analysis=routing,
            satellite_data=satellite_data,
            response_text=response_data,
            technical_metrics=technical_metrics,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing demo query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample-queries")
async def get_sample_queries():
    """Get predefined sample queries for testing"""
    try:
        demo = get_demo_system()
        return {
            "status": "success",
            "sample_queries": demo.demo_queries
        }
    except Exception as e:
        logger.error(f"Error getting sample queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/satellite-data")
async def get_available_locations():
    """Get available satellite data locations"""
    try:
        demo = get_demo_system()
        locations = {}
        
        for location, data in demo.mock_satellite_data.items():
            locations[location] = {
                "name": location.replace("_", " ").title(),
                "environmental_score": data["environmental_score"],
                "risk_level": data["risk_level"],
                "ndvi": data["ndvi"]
            }
        
        return {
            "status": "success",
            "available_locations": locations
        }
    except Exception as e:
        logger.error(f"Error getting satellite data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def demo_health_check():
    """Health check for demo system"""
    try:
        demo = get_demo_system()
        return {
            "status": "healthy",
            "session_id": demo.session_id,
            "timestamp": datetime.now().isoformat(),
            "demo_mode": True,
            "mock_data": True
        }
    except Exception as e:
        logger.error(f"Demo health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
