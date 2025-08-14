"""
🛰️ Satellite Data Integration Utility for Agricultural Agents
=============================================================

This module provides satellite data integration capabilities for agricultural agents.
It allows agents to query and utilize real-time satellite data for enhanced decision-making.

Features:
- Location-based satellite data retrieval
- NDVI vegetation health assessment
- Soil moisture monitoring
- Weather pattern analysis
- Historical trend analysis
- Agricultural decision support

Author: Multi-Agent Agriculture System
Created: 2025-08-15
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add path for satellite service
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.satellite_service import create_satellite_pipeline, LocationData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SatelliteDataIntegrator:
    """
    🛰️ Satellite Data Integration for Agricultural Agents
    
    This class provides agricultural agents with access to satellite data
    for enhanced decision-making and environmental awareness.
    """
    
    def __init__(self):
        self.pipeline = create_satellite_pipeline()
        logger.info("🛰️ Satellite Data Integrator initialized")
    
    async def get_location_satellite_data(self, latitude: float, longitude: float, 
                                        location_name: str = None, days_back: int = 7) -> Dict:
        """
        Get comprehensive satellite data for a specific location
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            location_name: Human-readable location name
            days_back: Number of days of historical data to retrieve
            
        Returns:
            Dictionary containing satellite metrics and analysis
        """
        try:
            # Get location data from satellite pipeline
            location_data = self.pipeline.get_location_data(latitude, longitude, days_back)
            
            # If no data exists, generate current data
            if not location_data["latest_data"]:
                logger.info(f"🛰️ No existing data for {latitude}, {longitude}. Generating current data...")
                
                # Create location and acquire fresh data
                location = LocationData(
                    latitude=latitude,
                    longitude=longitude,
                    location_name=location_name or f"Location_{latitude}_{longitude}",
                    region=self._determine_region(latitude, longitude)
                )
                
                # Acquire current satellite data
                await self.pipeline.acquire_data_for_location(location)
                
                # Retrieve the newly acquired data
                location_data = self.pipeline.get_location_data(latitude, longitude, days_back)
            
            # Process and enhance data for agricultural use
            return self._process_agricultural_data(location_data, latitude, longitude)
            
        except Exception as e:
            logger.error(f"❌ Error retrieving satellite data for {latitude}, {longitude}: {e}")
            return self._create_fallback_data(latitude, longitude)
    
    def _determine_region(self, latitude: float, longitude: float) -> str:
        """Determine Indian region based on coordinates"""
        if latitude > 28:
            return "North India"
        elif latitude < 15:
            return "South India"
        else:
            return "Central/West India"
    
    def _process_agricultural_data(self, location_data: Dict, latitude: float, longitude: float) -> Dict:
        """Process satellite data for agricultural decision making"""
        
        agricultural_data = {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "region": self._determine_region(latitude, longitude)
            },
            "current_conditions": {},
            "vegetation_health": {},
            "irrigation_insights": {},
            "weather_patterns": {},
            "agricultural_recommendations": {},
            "data_quality": location_data.get("summary", {}).get("data_quality", "unknown"),
            "last_updated": None
        }
        
        # Process latest data if available
        if location_data["latest_data"]:
            latest = location_data["latest_data"][0]
            agricultural_data["last_updated"] = latest.get("timestamp")
            
            # Current conditions
            agricultural_data["current_conditions"] = {
                "ndvi": latest.get("ndvi", 0),
                "soil_moisture": latest.get("soil_moisture", 0),
                "temperature": latest.get("temperature", 0),
                "precipitation": latest.get("precipitation", 0),
                "vegetation_health": latest.get("vegetation_health", "Unknown")
            }
            
            # Vegetation health assessment
            ndvi = latest.get("ndvi", 0)
            agricultural_data["vegetation_health"] = self._assess_vegetation_health(ndvi)
            
            # Irrigation insights
            soil_moisture = latest.get("soil_moisture", 0)
            agricultural_data["irrigation_insights"] = self._generate_irrigation_insights(soil_moisture, latest.get("precipitation", 0))
            
            # Weather patterns
            agricultural_data["weather_patterns"] = self._analyze_weather_patterns(location_data["latest_data"][:7])
            
            # Agricultural recommendations
            agricultural_data["agricultural_recommendations"] = self._generate_agricultural_recommendations(
                ndvi, soil_moisture, latest.get("temperature", 0), latest.get("precipitation", 0)
            )
        
        # Process trends if available
        if location_data.get("trends") and location_data["trends"].get("summary"):
            trends = location_data["trends"]["summary"]
            agricultural_data["trends"] = {
                "direction": trends.get("trend_direction", "stable"),
                "average_ndvi": trends.get("avg_ndvi", 0),
                "max_ndvi": trends.get("max_ndvi", 0),
                "min_ndvi": trends.get("min_ndvi", 0),
                "data_points": trends.get("data_points", 0)
            }
        
        return agricultural_data
    
    def _assess_vegetation_health(self, ndvi: float) -> Dict:
        """Assess vegetation health based on NDVI"""
        if ndvi > 0.7:
            health_status = "Excellent"
            health_description = "Dense, healthy vegetation with optimal photosynthetic activity"
            color_code = "🟢"
        elif ndvi > 0.5:
            health_status = "Good"
            health_description = "Healthy vegetation with good growth potential"
            color_code = "🟡"
        elif ndvi > 0.3:
            health_status = "Fair"
            health_description = "Moderate vegetation with room for improvement"
            color_code = "🟠"
        elif ndvi > 0.1:
            health_status = "Poor"
            health_description = "Sparse vegetation requiring attention"
            color_code = "🔴"
        else:
            health_status = "Critical"
            health_description = "Very poor vegetation or bare soil"
            color_code = "⚫"
        
        return {
            "status": health_status,
            "description": health_description,
            "color_code": color_code,
            "ndvi_value": ndvi,
            "recommendations": self._get_vegetation_recommendations(health_status)
        }
    
    def _get_vegetation_recommendations(self, health_status: str) -> List[str]:
        """Get recommendations based on vegetation health"""
        recommendations = {
            "Excellent": [
                "Continue current agricultural practices",
                "Consider harvesting timing for optimal yield",
                "Monitor for pest activity due to dense vegetation"
            ],
            "Good": [
                "Maintain regular irrigation schedule",
                "Apply balanced fertilizers if needed",
                "Monitor growth progress weekly"
            ],
            "Fair": [
                "Increase irrigation frequency if soil moisture is low",
                "Apply nitrogen-rich fertilizers to boost growth",
                "Check for pest or disease issues"
            ],
            "Poor": [
                "Immediate soil testing recommended",
                "Increase irrigation and nutrients",
                "Consider crop protection measures"
            ],
            "Critical": [
                "Emergency intervention required",
                "Soil analysis and remediation needed",
                "Consider replanting if necessary"
            ]
        }
        return recommendations.get(health_status, ["Monitor vegetation closely"])
    
    def _generate_irrigation_insights(self, soil_moisture: float, recent_precipitation: float) -> Dict:
        """Generate irrigation insights based on soil moisture and precipitation"""
        
        # Determine irrigation need
        if soil_moisture > 70:
            irrigation_need = "Low"
            recommendation = "Soil moisture is adequate. Monitor for waterlogging."
            urgency = "none"
        elif soil_moisture > 40:
            irrigation_need = "Moderate" 
            recommendation = "Soil moisture is good. Light irrigation may be beneficial."
            urgency = "low"
        elif soil_moisture > 20:
            irrigation_need = "High"
            recommendation = "Soil moisture is declining. Irrigation recommended within 24-48 hours."
            urgency = "medium"
        else:
            irrigation_need = "Critical"
            recommendation = "Soil moisture is critically low. Immediate irrigation required."
            urgency = "high"
        
        # Adjust for recent precipitation
        if recent_precipitation > 10:
            recommendation += f" Recent rainfall ({recent_precipitation:.1f}mm) may reduce immediate need."
            if urgency == "high":
                urgency = "medium"
            elif urgency == "medium":
                urgency = "low"
        
        return {
            "irrigation_need": irrigation_need,
            "urgency": urgency,
            "soil_moisture_percent": soil_moisture,
            "recent_precipitation_mm": recent_precipitation,
            "recommendation": recommendation,
            "optimal_moisture_range": "40-70%",
            "water_stress_indicator": "High" if soil_moisture < 25 else "Low"
        }
    
    def _analyze_weather_patterns(self, recent_data: List[Dict]) -> Dict:
        """Analyze recent weather patterns"""
        if not recent_data:
            return {"status": "No recent data available"}
        
        # Extract weather metrics
        temperatures = [d.get("temperature", 0) for d in recent_data]
        precipitation_values = [d.get("precipitation", 0) for d in recent_data]
        
        avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0
        total_precipitation = sum(precipitation_values)
        
        # Determine weather trend
        if len(temperatures) >= 3:
            recent_temp_avg = sum(temperatures[:3]) / 3
            older_temp_avg = sum(temperatures[3:]) / max(1, len(temperatures[3:]))
            temp_trend = "Rising" if recent_temp_avg > older_temp_avg + 1 else "Falling" if recent_temp_avg < older_temp_avg - 1 else "Stable"
        else:
            temp_trend = "Insufficient data"
        
        return {
            "average_temperature": round(avg_temp, 1),
            "total_precipitation_7days": round(total_precipitation, 1),
            "temperature_trend": temp_trend,
            "precipitation_category": "High" if total_precipitation > 50 else "Moderate" if total_precipitation > 10 else "Low",
            "weather_suitability": self._assess_weather_suitability(avg_temp, total_precipitation)
        }
    
    def _assess_weather_suitability(self, avg_temp: float, total_precip: float) -> str:
        """Assess weather suitability for agriculture"""
        if 20 <= avg_temp <= 30 and 20 <= total_precip <= 100:
            return "Excellent for most crops"
        elif 15 <= avg_temp <= 35 and 10 <= total_precip <= 150:
            return "Good for agriculture"
        elif avg_temp > 35 or total_precip > 200:
            return "Challenging conditions - heat/flood risk"
        elif avg_temp < 10 or total_precip < 5:
            return "Challenging conditions - cold/drought risk"
        else:
            return "Moderate conditions"
    
    def _generate_agricultural_recommendations(self, ndvi: float, soil_moisture: float, 
                                            temperature: float, precipitation: float) -> Dict:
        """Generate comprehensive agricultural recommendations"""
        
        recommendations = {
            "crop_management": [],
            "irrigation": [],
            "fertilization": [],
            "pest_disease": [],
            "general": []
        }
        
        # Crop management recommendations based on NDVI
        if ndvi > 0.7:
            recommendations["crop_management"].append("Crops are thriving - monitor for harvest readiness")
        elif ndvi < 0.3:
            recommendations["crop_management"].append("Poor vegetation health - investigate soil/plant issues")
        
        # Irrigation recommendations based on soil moisture
        if soil_moisture < 25:
            recommendations["irrigation"].append("Urgent irrigation needed - soil moisture critically low")
        elif soil_moisture < 40:
            recommendations["irrigation"].append("Schedule irrigation within 1-2 days")
        
        # Temperature-based recommendations
        if temperature > 35:
            recommendations["general"].append("High temperature alert - provide shade/cooling if possible")
        elif temperature < 10:
            recommendations["general"].append("Cold weather - protect sensitive crops")
        
        # Precipitation-based recommendations
        if precipitation > 50:
            recommendations["general"].append("Heavy rainfall - ensure proper drainage")
            recommendations["pest_disease"].append("Monitor for fungal diseases after heavy rain")
        
        return recommendations
    
    def _create_fallback_data(self, latitude: float, longitude: float) -> Dict:
        """Create fallback data when satellite data is unavailable"""
        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "region": self._determine_region(latitude, longitude)
            },
            "current_conditions": {
                "ndvi": 0.5,  # Default moderate value
                "soil_moisture": 30,  # Default moderate value
                "temperature": 25,  # Default moderate value
                "precipitation": 5,  # Default low value
                "vegetation_health": "Unknown"
            },
            "vegetation_health": {
                "status": "Unknown",
                "description": "Satellite data unavailable",
                "color_code": "⚪",
                "ndvi_value": 0.5,
                "recommendations": ["Satellite data unavailable - use local observations"]
            },
            "irrigation_insights": {
                "irrigation_need": "Monitor locally",
                "urgency": "unknown",
                "recommendation": "Satellite data unavailable - check soil manually"
            },
            "weather_patterns": {
                "status": "Data unavailable"
            },
            "agricultural_recommendations": {
                "general": ["Use local weather and soil observations"]
            },
            "data_quality": "unavailable",
            "last_updated": None,
            "error": "Satellite data service unavailable"
        }

# Global satellite integrator instance
satellite_integrator = None

def get_satellite_integrator() -> SatelliteDataIntegrator:
    """Get or create the global satellite integrator instance"""
    global satellite_integrator
    if satellite_integrator is None:
        satellite_integrator = SatelliteDataIntegrator()
    return satellite_integrator

async def get_satellite_data_for_location(latitude: float, longitude: float, 
                                        location_name: str = None) -> Dict:
    """
    Convenience function for agents to get satellite data
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        location_name: Optional location name
        
    Returns:
        Processed satellite data for agricultural decision making
    """
    integrator = get_satellite_integrator()
    return await integrator.get_location_satellite_data(latitude, longitude, location_name)

def format_satellite_summary(satellite_data: Dict) -> str:
    """
    Format satellite data into a readable summary for agents
    
    Args:
        satellite_data: Processed satellite data dictionary
        
    Returns:
        Formatted string summary
    """
    if satellite_data.get("error"):
        return f"🛰️ Satellite data unavailable: {satellite_data['error']}"
    
    conditions = satellite_data.get("current_conditions", {})
    vegetation = satellite_data.get("vegetation_health", {})
    irrigation = satellite_data.get("irrigation_insights", {})
    
    summary = f"""🛰️ SATELLITE DATA SUMMARY:
📍 Location: {satellite_data['location']['latitude']:.4f}°N, {satellite_data['location']['longitude']:.4f}°E
🌱 Vegetation Health: {vegetation.get('color_code', '⚪')} {vegetation.get('status', 'Unknown')} (NDVI: {conditions.get('ndvi', 0):.3f})
💧 Soil Moisture: {conditions.get('soil_moisture', 0):.1f}% ({irrigation.get('irrigation_need', 'Unknown')} irrigation need)
🌡️ Temperature: {conditions.get('temperature', 0):.1f}°C
🌧️ Recent Precipitation: {conditions.get('precipitation', 0):.1f}mm
⚡ Data Quality: {satellite_data.get('data_quality', 'Unknown')}"""
    
    # Add key recommendations
    recommendations = satellite_data.get("agricultural_recommendations", {})
    if recommendations:
        summary += "\n\n🎯 KEY RECOMMENDATIONS:"
        for category, recs in recommendations.items():
            if recs:
                summary += f"\n• {recs[0]}"
    
    return summary

# Export key functions
__all__ = [
    "SatelliteDataIntegrator",
    "get_satellite_integrator", 
    "get_satellite_data_for_location",
    "format_satellite_summary"
]
