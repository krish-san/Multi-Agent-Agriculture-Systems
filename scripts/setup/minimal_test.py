"""
Minimal test to check basic functionality
"""

def test_basic_imports():
    print("Testing basic Python functionality...")
    
    try:
        # Test basic enum creation
        from enum import Enum
        
        class TestEnum(str, Enum):
            VALUE1 = "value1"
            VALUE2 = "value2"
        
        print("✓ Enum creation works")
        
        # Test dataclass
        from dataclasses import dataclass
        
        @dataclass
        class TestData:
            name: str
            value: int = 0
        
        test_obj = TestData("test", 42)
        print("✓ Dataclass creation works")
        
        # Test pydantic
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int = 0
        
        test_model = TestModel(name="test", value=42)
        print("✓ Pydantic model works")
        
        # Test asyncio
        import asyncio
        
        async def test_async():
            return "async works"
        
        result = asyncio.run(test_async())
        print("✓ Asyncio works")
        
        print("\n🎉 ALL BASIC PYTHON FEATURES WORK!")
        return True
        
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agentweaver_imports():
    print("\nTesting AgentWeaver imports...")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Test core models import
        from src.core.models import AgentStatus, TaskStatus
        print("✓ Core models imported")
        
        # Test specific imports one by one
        from src.core.models import AgentCapability
        print("✓ AgentCapability imported")
        
        print("\n🎉 AGENTWEAVER IMPORTS WORK!")
        return True
        
    except Exception as e:
        print(f"✗ AgentWeaver import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    basic_success = test_basic_imports()
    if basic_success:
        agentweaver_success = test_agentweaver_imports()
        exit(0 if agentweaver_success else 1)
    else:
        exit(1)
