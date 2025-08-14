#!/usr/bin/env python3
"""
Simple test for irrigation agent satellite integration
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.agriculture_models import AgricultureQuery, Location
from src.agents.irrigation_agent import IrrigationAgent

async def simple_irrigation_test():
    """Simple test for irrigation agent"""
    print("💧 Simple Irrigation Agent Test")
    print("=" * 40)
    
    try:
        # Initialize the agent
        print("Creating irrigation agent...")
        agent = IrrigationAgent()
        print(f"✅ Agent created: {agent.name}")
        print(f"🆔 Agent ID: {agent.agent_id}")
        print(f"🎯 Capabilities: {[cap.value for cap in agent.agent_state.capabilities]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_irrigation_test())
    print(f"\n{'✅ Success!' if success else '❌ Failed!'}")
