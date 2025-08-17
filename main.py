
import sys
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging


# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestration.supervisor import SupervisorNode
from src.core.redis_config import RedisConnectionManager
from src.api.models import SystemStatusResponse
from src.agents.harvest_planning_agent import HarvestPlanningAgent
from src.core.agriculture_models import AgricultureQuery, Language, Location
from src.api.routers import agriculture
# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AgentWeaver server...")
    
    # Initialize Redis connection
    app.state.redis_manager = RedisConnectionManager()
    logger.info("Redis manager is ready")
    
    # Initialize supervisor
    app.state.supervisor = SupervisorNode()
    logger.info("Supervisor is ready")
    
    # Initialize WebSocket manager
    from src.services.websocket_manager import WebSocketManager
    from src.services.websocket_integration import integration_service
    app.state.ws_manager = WebSocketManager()
    
    # Connect integration service to WebSocket manager
    integration_service.set_websocket_manager(app.state.ws_manager)
    
    logger.info("WebSocket system is ready")
    logger.info("AgentWeaver server is fully operational")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AgentWeaver server...")
    
    # Cleanup connections
    if hasattr(app.state, 'ws_manager'):
        await app.state.ws_manager.disconnect_all()
        logger.info("All WebSocket connections closed")
    
    logger.info("AgentWeaver shutdown complete")


# FastAPI application
app = FastAPI(
    title="AgentWeaver API",
    description="Multi-agent orchestration platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AgentWeaver API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"], response_model=SystemStatusResponse)
async def health_check():
    try:
        # Check Redis
        redis_status = "connected" if app.state.redis_manager.test_connection() else "disconnected"
        
        # Check supervisor
        supervisor_status = "initialized" if hasattr(app.state, 'supervisor') else "not_initialized"
        
        # Check WebSocket manager
        ws_status = "initialized" if hasattr(app.state, 'ws_manager') else "not_initialized"
        ws_connections = len(app.state.ws_manager.active_connections) if hasattr(app.state, 'ws_manager') else 0
        
        return SystemStatusResponse(
            status="healthy",
            uptime=0.0,  # Track actual uptime
            version="1.0.0",
            timestamp=datetime.now(),
            services={
                "redis": redis_status,
                "supervisor": supervisor_status,
                "websocket_manager": ws_status
            },
            metrics={
                "active_websocket_connections": ws_connections,
                "active_agents": 0,  # Get from supervisor
                "running_workflows": 0  # Get from supervisor
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Include routers
from src.api.routers import agents, workflows, websocket
from src.api.routers.agriculture import router as agriculture_router
from src.api.satellite_api import router as satellite_router

app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(websocket.router)
app.include_router(agriculture_router)
app.include_router(satellite_router)

@app.get("/api/info", tags=["Info"])
async def api_info():
    return {
        "api": "AgentWeaver",
        "version": "1.0.0",
        "endpoints": {
            "agents": "/agents - Manage agents",
            "workflows": "/workflows - Control workflows", 
            "websocket": "/ws/updates - Real-time updates"
        },
        "status": "ready"
    }

@app.post("/api/test/demo-workflow", tags=["Testing"])
async def trigger_demo_workflow():
    """Trigger a demo workflow that sends real-time updates to the dashboard"""
    try:
        from src.services.websocket_integration import integration_service
        import asyncio
        import time
        
        # Create demo workflow
        workflow_id = f"demo_workflow_{int(time.time())}"
        
        # Start workflow
        await integration_service.notify_workflow_started(workflow_id, {
            "estimated_steps": 3,
            "input_data": {
                "text": "Demo customer review analysis",
                "metadata": {"source": "dashboard_demo"}
            }
        })
        
        # Update agents and workflow steps with delays
        asyncio.create_task(_run_demo_workflow_async(workflow_id))
        
        return {
            "message": "Demo workflow started",
            "workflow_id": workflow_id,
            "check_dashboard": "Watch your dashboard for real-time updates!"
        }
        
    except Exception as e:
        logger.error(f"Failed to start demo workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_demo_workflow_async(workflow_id: str):
    """Run the demo workflow asynchronously with realistic timing"""
    try:
        from src.services.websocket_integration import integration_service
        import time
        
        # Step 1: Text Analysis
        await integration_service.notify_agent_status_change(
            "text_analyzer", "idle", "busy", 
            {"current_task": "Analyzing customer sentiment"}
        )
        await asyncio.sleep(2)
        
        await integration_service.notify_workflow_step(
            workflow_id, "text_analysis", {
                "sentiment": "positive",
                "confidence": 0.87
            }
        )
        
        # Step 2: Data Processing
        await integration_service.notify_agent_status_change(
            "data_processor", "idle", "busy",
            {"current_task": "Processing customer data"}
        )
        await asyncio.sleep(2)
        
        await integration_service.notify_workflow_step(
            workflow_id, "data_processing", {
                "records_processed": 1247,
                "data_quality": "high"
            }
        )
        
        # Step 3: API Integration  
        await integration_service.notify_agent_status_change(
            "api_client", "idle", "busy",
            {"current_task": "Fetching external data"}
        )
        await asyncio.sleep(2)
        
        await integration_service.notify_workflow_step(
            workflow_id, "api_integration", {
                "external_data": "retrieved",
                "api_calls": 3
            }
        )
        
        # Complete workflow
        await integration_service.notify_workflow_completed(workflow_id, {
            "status": "completed",
            "total_sentiment_score": 0.87,
            "records_processed": 1247,
            "summary": "Customer review analysis completed successfully"
        })
        
        # Reset agents to idle
        for agent_id in ["text_analyzer", "data_processor", "api_client"]:
            await integration_service.notify_agent_status_change(
                agent_id, "busy", "idle", {"current_task": None}
            )
            
    except Exception as e:
        logger.error(f"Error in demo workflow {workflow_id}: {e}")


if __name__ == "__main__":
    # Run server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
