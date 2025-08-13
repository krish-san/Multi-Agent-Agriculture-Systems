"""
Simple integration test to verify core functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.agriculture_models import AgricultureQuery, QueryDomain, Language
from src.agents.agriculture_router import AgricultureRouter
from src.agents.crop_selection_agent import CropSelectionAgent

def test_basic_functionality():
    print("Testing basic system functionality...")
    
    try:
        # Test 1: Create a simple query
        print("1. Creating agriculture query...")
        query = AgricultureQuery(
            query_text="What wheat variety is best for Punjab?",
            query_language=Language.ENGLISH,
            user_id="test_user"
        )
        print("✓ Query created successfully")
        
        # Test 2: Initialize router
        print("2. Initializing agriculture router...")
        router = AgricultureRouter()
        print("✓ Router initialized successfully")
        
        # Test 3: Initialize crop agent
        print("3. Initializing crop selection agent...")
        crop_agent = CropSelectionAgent()
        print("✓ Crop agent initialized successfully")
        
        # Test 4: Test pattern-based classification
        print("4. Testing query classification...")
        import asyncio
        
        async def test_classification():
            domain = await router._classify_query_pattern_based(query)
            return domain
        
        domain = asyncio.run(test_classification())
        print(f"✓ Query classified as: {domain.value}")
        
        # Test 5: Test crop agent processing
        print("5. Testing crop agent query processing...")
        
        async def test_processing():
            response = await crop_agent.process_query(query)
            return response
        
        response = asyncio.run(test_processing())
        print(f"✓ Agent processed query with confidence: {response.confidence:.2f}")
        print(f"✓ Generated {len(response.recommendations)} recommendations")
        
        print("\n🎉 ALL BASIC TESTS PASSED!")
        print("The multi-agent agriculture system is functional!")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    exit(0 if success else 1)
