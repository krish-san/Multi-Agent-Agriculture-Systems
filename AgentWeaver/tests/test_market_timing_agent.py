"""
Test script for Market Timing Agent (Standalone)
"""
import sys
import os
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional

# Ensure the source directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# --- Mock objects required for the agent to run ---

class Language(Enum):
    ENGLISH = "english"
    HINDI = "hindi"
    MIXED = "mixed"

class CropType(Enum):
    WHEAT = "wheat"
    ONION = "onion"

class QueryDomain(Enum):
    GENERAL = "general"

@dataclass
class Location:
    state: str
    district: str

@dataclass
class AgricultureQuery:
    query_text: str
    query_language: Language
    user_id: str
    query_id: str = "test_query"
    location: Optional[Location] = None
    farm_profile: Optional[Any] = None
    domain: QueryDomain = QueryDomain.GENERAL

@dataclass
class AgentResponse:
    agent_id: str
    agent_name: str
    query_id: str
    response_text: str
    response_language: Language
    confidence_score: float
    reasoning: str = ""
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

class BaseAgent:
    """Mock BaseAgent class"""
    def __init__(self):
        self.agent_id = "base_mock"
        self.capabilities = []

# --- Create mock modules to satisfy agent's imports ---
import types

# Mock for core.agriculture_models
ag_models_mock = types.ModuleType('core.agriculture_models')
ag_models_mock.AgricultureQuery = AgricultureQuery
ag_models_mock.AgentResponse = AgentResponse
ag_models_mock.CropType = CropType
ag_models_mock.Location = Location
ag_models_mock.QueryDomain = QueryDomain
ag_models_mock.Language = Language
sys.modules['core.agriculture_models'] = ag_models_mock

# Mock for agents.base_agent
base_agent_mock = types.ModuleType('agents.base_agent')
base_agent_mock.BaseAgent = BaseAgent
sys.modules['agents.base_agent'] = base_agent_mock

# --- Import the agent to be tested ---
from agents.market_timing_agent import MarketTimingAgent, Commodity

async def main():
    """Main function to run the test suite"""
    agent = MarketTimingAgent()
    
    print("📈 Testing Market Timing Agent")
    
    # Test 1: English query for Wheat
    query_en = AgricultureQuery(
        query_text="What is the price forecast for wheat?",
        query_language=Language.ENGLISH,
        user_id="test_farmer_en",
        location=Location(state="Punjab", district="Amritsar")
    )
    
    print("\n🔄 Processing English query for Wheat...")
    response_en = await agent.process_query(query_en)
    print(f"✅ English Response: {response_en.response_text}")
    assert response_en.confidence_score > 0.7
    assert "Wheat" in response_en.response_text or "गेहूं" in response_en.response_text

    # Test 2: Hindi query for Onion
    query_hi = AgricultureQuery(
        query_text="प्याज का भाव क्या रहेगा?",
        query_language=Language.HINDI,
        user_id="test_farmer_hi",
        location=Location(state="Maharashtra", district="Nashik")
    )
    
    print("\n🔄 Processing Hindi query for Onion...")
    response_hi = await agent.process_query(query_hi)
    print(f"✅ Hindi Response: {response_hi.response_text}")
    assert response_hi.confidence_score > 0.7
    assert "प्याज" in response_hi.response_text

    # Test 3: General query with no commodity
    query_general = AgricultureQuery(
        query_text="What is the market trend?",
        query_language=Language.ENGLISH,
        user_id="test_farmer_gen"
    )
    print("\n🔄 Processing general query...")
    response_gen = await agent.process_query(query_general)
    print(f"✅ General Response: {response_gen.response_text}")
    assert "Please specify a commodity" in response_gen.response_text

    # Test 4: Check internal forecast generation
    print("\n🔄 Testing internal forecast generation for Cotton...")
    forecast = agent._generate_price_forecast(Commodity.COTTON)
    print(f"✅ Forecast for Cotton: Current Price ₹{forecast.current_price}, 7D Forecast ₹{forecast.forecast_price_7d}")
    assert forecast.current_price > 0
    assert forecast.forecast_price_7d > 0

    print("\n🎉 Market Timing Agent working successfully!")

if __name__ == "__main__":
    asyncio.run(main())
