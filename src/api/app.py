"""
FastAPI Main Application
Multi-Agent Agriculture Systems API
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import routers
from .routers.agriculture import router as agriculture_router
from .routers.demo import router as demo_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Agriculture Systems API",
    description="Satellite-Enhanced AI Agricultural Advisory System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agriculture_router)
app.include_router(demo_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🌾🛰️ Multi-Agent Agriculture Systems API",
        "status": "online",
        "version": "1.0.0",
        "description": "Satellite-Enhanced AI Agricultural Advisory System",
        "endpoints": {
            "agriculture": "/agriculture/*",
            "demo": "/demo/*",
            "docs": "/docs",
            "health": "/health"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "online",
            "demo": "available",
            "agriculture": "available"
        }
    }

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "available_endpoints": [
                "/",
                "/health", 
                "/demo/capabilities",
                "/demo/query",
                "/agriculture/query",
                "/docs"
            ]
        }
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "Please check the logs for more details"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
