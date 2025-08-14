"""
🌐 Satellite Data API Integration
=================================

FastAPI endpoints for satellite data acquisition and retrieval.
Integrates with the satellite service to provide RESTful access.

Author: Multi-Agent Agriculture System
Created: 2025-01-XX
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime, timedelta

from ..services.satellite_service import (
    SatelliteDataPipeline, 
    LocationData, 
    create_satellite_pipeline
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize global pipeline
satellite_pipeline = create_satellite_pipeline()

# Pydantic models for API
class LocationRequest(BaseModel):
    """Location request model"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    location_name: Optional[str] = Field(None, description="Human-readable location name")
    region: Optional[str] = Field(None, description="Region or state")
    elevation: Optional[float] = Field(None, description="Elevation in meters")

class SatelliteDataRequest(BaseModel):
    """Request model for satellite data acquisition"""
    location: LocationRequest
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format (default: today)")
    crop_type: str = Field("mixed", description="Crop type for specialized analysis")

class BulkAcquisitionRequest(BaseModel):
    """Request model for bulk data acquisition"""
    days_back: int = Field(7, ge=1, le=365, description="Number of days to acquire data for")
    locations: Optional[List[LocationRequest]] = Field(None, description="Specific locations (default: all monitoring locations)")

class SatelliteDataResponse(BaseModel):
    """Response model for satellite data"""
    success: bool
    timestamp: str
    location: Dict
    metrics: Dict
    source: str
    message: str

class LocationDataResponse(BaseModel):
    """Response model for location data retrieval"""
    location: Dict
    latest_data: List[Dict]
    trends: Dict
    summary: Dict

# Create router
router = APIRouter(prefix="/api/satellite", tags=["satellite"])

@router.get("/health", summary="Check satellite service health")
async def health_check():
    """Check if the satellite data service is operational"""
    try:
        # Test database connection
        test_data = satellite_pipeline.get_location_data(28.7041, 77.1025, days_back=1)
        
        return {
            "status": "healthy",
            "service": "Satellite Data Acquisition",
            "version": "1.0.0",
            "database": "connected",
            "monitoring_locations": len(satellite_pipeline.monitoring_locations),
            "message": "🛰️ Satellite service is operational"
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@router.post("/acquire", response_model=SatelliteDataResponse, summary="Acquire satellite data for a location")
async def acquire_satellite_data(request: SatelliteDataRequest):
    """
    🛰️ Acquire satellite data for a specific location and date
    
    This endpoint simulates satellite data acquisition including:
    - NDVI (vegetation health)
    - Soil moisture
    - Weather conditions
    - Vegetation assessment
    """
    try:
        # Create location data
        location = LocationData(
            latitude=request.location.latitude,
            longitude=request.location.longitude,
            location_name=request.location.location_name or f"Location_{request.location.latitude}_{request.location.longitude}",
            region=request.location.region or "Unknown",
            elevation=request.location.elevation
        )
        
        # Parse date if provided
        date = datetime.now()
        if request.date:
            try:
                date = datetime.strptime(request.date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Acquire data
        data_point = await satellite_pipeline.acquire_data_for_location(
            location=location,
            date=date,
            crop_type=request.crop_type
        )
        
        return SatelliteDataResponse(
            success=True,
            timestamp=data_point.timestamp.isoformat(),
            location={
                "latitude": data_point.location.latitude,
                "longitude": data_point.location.longitude,
                "name": data_point.location.location_name,
                "region": data_point.location.region
            },
            metrics={
                "ndvi": data_point.metrics.ndvi,
                "soil_moisture": data_point.metrics.soil_moisture,
                "temperature": data_point.metrics.temperature,
                "precipitation": data_point.metrics.precipitation,
                "cloud_cover": data_point.metrics.cloud_cover,
                "vegetation_health": data_point.metrics.vegetation_health,
                "confidence_score": data_point.metrics.confidence_score
            },
            source=data_point.source,
            message=f"🛰️ Satellite data acquired successfully for {location.location_name}"
        )
        
    except Exception as e:
        logger.error(f"❌ Error acquiring satellite data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acquire satellite data: {str(e)}")

@router.post("/bulk-acquire", summary="Bulk acquire satellite data")
async def bulk_acquire_data(request: BulkAcquisitionRequest, background_tasks: BackgroundTasks):
    """
    🚀 Acquire satellite data in bulk for multiple locations and dates
    
    This is useful for:
    - Historical data simulation
    - System initialization
    - Research and analysis
    """
    try:
        # Start bulk acquisition in background
        background_tasks.add_task(
            satellite_pipeline.bulk_acquire_data,
            days_back=request.days_back
        )
        
        return {
            "success": True,
            "message": f"🚀 Bulk acquisition started for {request.days_back} days",
            "status": "processing",
            "locations": len(satellite_pipeline.monitoring_locations),
            "estimated_data_points": len(satellite_pipeline.monitoring_locations) * request.days_back
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting bulk acquisition: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bulk acquisition: {str(e)}")

@router.get("/data", response_model=LocationDataResponse, summary="Get satellite data for a location")
async def get_location_data(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    days_back: int = Query(7, ge=1, le=365, description="Number of days to retrieve")
):
    """
    📊 Retrieve satellite data for a specific location
    
    Returns:
    - Latest satellite measurements
    - Historical trends
    - Data quality assessment
    - Vegetation health summary
    """
    try:
        location_data = satellite_pipeline.get_location_data(latitude, longitude, days_back)
        
        return LocationDataResponse(
            location=location_data["location"],
            latest_data=location_data["latest_data"],
            trends=location_data["trends"],
            summary=location_data["summary"]
        )
        
    except Exception as e:
        logger.error(f"❌ Error retrieving location data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve location data: {str(e)}")

@router.get("/locations", summary="Get monitoring locations")
async def get_monitoring_locations():
    """
    📍 Get all predefined monitoring locations
    
    Returns the list of locations where satellite data is automatically collected.
    """
    try:
        locations = []
        for loc in satellite_pipeline.monitoring_locations:
            locations.append({
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "name": loc.location_name,
                "region": loc.region,
                "elevation": loc.elevation
            })
        
        return {
            "success": True,
            "locations": locations,
            "count": len(locations),
            "message": f"📍 {len(locations)} monitoring locations available"
        }
        
    except Exception as e:
        logger.error(f"❌ Error retrieving monitoring locations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve monitoring locations: {str(e)}")

@router.get("/trends/{location_name}", summary="Get trends for a specific monitoring location")
async def get_location_trends(
    location_name: str,
    months_back: int = Query(12, ge=1, le=60, description="Number of months for trend analysis")
):
    """
    📈 Get detailed trends for a specific monitoring location
    
    Provides historical trends and patterns for agricultural decision making.
    """
    try:
        # Find location by name
        target_location = None
        for loc in satellite_pipeline.monitoring_locations:
            if loc.location_name.lower() == location_name.lower():
                target_location = loc
                break
        
        if not target_location:
            raise HTTPException(status_code=404, detail=f"Location '{location_name}' not found in monitoring locations")
        
        # Get trends
        trends = satellite_pipeline.storage.get_historical_trends(
            target_location.latitude,
            target_location.longitude,
            months_back
        )
        
        return {
            "success": True,
            "location": {
                "name": target_location.location_name,
                "latitude": target_location.latitude,
                "longitude": target_location.longitude,
                "region": target_location.region
            },
            "trends": trends,
            "analysis_period": f"{months_back} months",
            "message": f"📈 Trends retrieved for {location_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving trends for {location_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}")

@router.post("/monitoring/start", summary="Start continuous monitoring")
async def start_monitoring(
    interval_hours: int = Query(6, ge=1, le=24, description="Monitoring interval in hours"),
    background_tasks: BackgroundTasks = None
):
    """
    🔄 Start continuous satellite data monitoring
    
    Begins automated data collection for all monitoring locations.
    """
    try:
        if satellite_pipeline.is_running:
            return {
                "success": False,
                "message": "🔄 Monitoring is already running",
                "status": "already_running"
            }
        
        # Start monitoring in background
        if background_tasks:
            background_tasks.add_task(
                satellite_pipeline.start_continuous_monitoring,
                interval_hours=interval_hours
            )
        
        return {
            "success": True,
            "message": f"🔄 Continuous monitoring started (every {interval_hours} hours)",
            "status": "started",
            "interval_hours": interval_hours,
            "monitoring_locations": len(satellite_pipeline.monitoring_locations)
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/monitoring/stop", summary="Stop continuous monitoring")
async def stop_monitoring():
    """
    🛑 Stop continuous satellite data monitoring
    """
    try:
        satellite_pipeline.stop_monitoring()
        
        return {
            "success": True,
            "message": "🛑 Continuous monitoring stopped",
            "status": "stopped"
        }
        
    except Exception as e:
        logger.error(f"❌ Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.get("/monitoring/status", summary="Get monitoring status")
async def get_monitoring_status():
    """
    📊 Get current monitoring status and statistics
    """
    try:
        # Get database statistics
        conn = satellite_pipeline.storage._get_connection() if hasattr(satellite_pipeline.storage, '_get_connection') else None
        total_records = 0
        
        if hasattr(satellite_pipeline.storage, 'db_path'):
            import sqlite3
            try:
                conn = sqlite3.connect(satellite_pipeline.storage.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM satellite_data")
                total_records = cursor.fetchone()[0]
                conn.close()
            except:
                pass
        
        return {
            "success": True,
            "monitoring": {
                "is_running": satellite_pipeline.is_running,
                "monitoring_locations": len(satellite_pipeline.monitoring_locations),
                "total_data_records": total_records
            },
            "database": {
                "status": "connected",
                "total_records": total_records
            },
            "message": f"🛰️ Monitoring status: {'Running' if satellite_pipeline.is_running else 'Stopped'}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")

# Export router for main app
__all__ = ["router"]
