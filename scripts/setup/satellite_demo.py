"""
🛰️ Satellite Data Acquisition System - Live Demo
===============================================

Interactive demonstration of the satellite data acquisition pipeline.
Shows real-time data generation, storage, and retrieval capabilities.

Author: Multi-Agent Agriculture System
Created: 2025-01-XX
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.satellite_service import (
    create_satellite_pipeline,
    LocationData
)

class SatelliteDemo:
    """Interactive satellite system demonstration"""
    
    def __init__(self):
        self.pipeline = create_satellite_pipeline()
        self.demo_locations = [
            LocationData(28.7041, 77.1025, "Delhi", "NCR", 216),
            LocationData(30.9010, 75.8573, "Ludhiana", "Punjab", 247),
            LocationData(13.0827, 80.2707, "Chennai", "Tamil Nadu", 6),
            LocationData(21.1458, 79.0882, "Nagpur", "Maharashtra", 310)
        ]
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 60)
        print(f"🛰️ {title}")
        print("=" * 60)
    
    def print_data_point(self, data_point, location_name: str):
        """Print formatted satellite data point"""
        metrics = data_point.metrics
        print(f"\n📍 {location_name}")
        print(f"   📊 NDVI: {metrics.ndvi:.3f} ({metrics.vegetation_health})")
        print(f"   💧 Soil Moisture: {metrics.soil_moisture:.1f}%")
        print(f"   🌡️ Temperature: {metrics.temperature:.1f}°C")
        print(f"   🌧️ Precipitation: {metrics.precipitation:.1f}mm")
        print(f"   ☁️ Cloud Cover: {metrics.cloud_cover:.1f}%")
        print(f"   🎯 Confidence: {metrics.confidence_score:.2f}")
        print(f"   ⏰ Timestamp: {data_point.timestamp.strftime('%Y-%m-%d %H:%M')}")
    
    async def demo_real_time_acquisition(self):
        """Demonstrate real-time satellite data acquisition"""
        self.print_header("REAL-TIME SATELLITE DATA ACQUISITION")
        
        print("\n🚀 Acquiring current satellite data for major agricultural regions...")
        
        for i, location in enumerate(self.demo_locations, 1):
            print(f"\n[{i}/{len(self.demo_locations)}] Processing {location.location_name}...")
            
            try:
                # Acquire current data
                data_point = await self.pipeline.acquire_data_for_location(location)
                self.print_data_point(data_point, location.location_name)
                
                # Small delay for visual effect
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Error acquiring data for {location.location_name}: {e}")
        
        print("\n✅ Real-time acquisition complete!")
    
    async def demo_historical_simulation(self):
        """Demonstrate historical data simulation"""
        self.print_header("HISTORICAL DATA SIMULATION")
        
        print("\n📈 Generating historical satellite data for the past 30 days...")
        
        # Use Delhi as example
        demo_location = self.demo_locations[0]
        historical_data = []
        
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            
            # Simulate different crop types throughout the season
            if i < 10:
                crop_type = "wheat"
            elif i < 20:
                crop_type = "rice"
            else:
                crop_type = "mixed"
            
            data_point = await self.pipeline.acquire_data_for_location(
                demo_location, date, crop_type
            )
            historical_data.append(data_point)
            
            if i % 5 == 0:  # Show progress every 5 days
                print(f"   📅 Generated data for {date.strftime('%Y-%m-%d')} (NDVI: {data_point.metrics.ndvi:.3f})")
        
        print(f"\n✅ Generated {len(historical_data)} historical data points!")
        
        # Show trends
        print("\n📊 NDVI Trend Analysis:")
        ndvi_values = [d.metrics.ndvi for d in reversed(historical_data[-10:])]
        for i, ndvi in enumerate(ndvi_values):
            date = (datetime.now() - timedelta(days=9-i)).strftime('%m-%d')
            bar_length = int(ndvi * 20)  # Scale for visualization
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"   {date}: {bar} {ndvi:.3f}")
    
    def demo_location_analysis(self):
        """Demonstrate comprehensive location analysis"""
        self.print_header("LOCATION-BASED ANALYSIS")
        
        print("\n🌍 Analyzing satellite data across different Indian regions...")
        
        for location in self.demo_locations:
            print(f"\n📍 {location.location_name}, {location.region}")
            
            # Get comprehensive data
            location_data = self.pipeline.get_location_data(
                location.latitude,
                location.longitude,
                days_back=7
            )
            
            summary = location_data["summary"]
            trends = location_data["trends"]
            
            print(f"   📊 Data Points Available: {summary['data_points_available']}")
            print(f"   🏆 Data Quality: {summary['data_quality'].title()}")
            
            if location_data["latest_data"]:
                latest = location_data["latest_data"][0]
                print(f"   🌱 Current NDVI: {latest['ndvi']:.3f}")
                print(f"   💧 Current Soil Moisture: {latest['soil_moisture']:.1f}%")
                print(f"   🏥 Vegetation Health: {latest['vegetation_health']}")
            
            if trends and "summary" in trends:
                trend_summary = trends["summary"]
                if "trend_direction" in trend_summary:
                    direction_emoji = {
                        "improving": "📈",
                        "declining": "📉", 
                        "stable": "➡️"
                    }.get(trend_summary["trend_direction"], "➡️")
                    
                    print(f"   📈 Trend: {direction_emoji} {trend_summary['trend_direction'].title()}")
                    if "avg_ndvi" in trend_summary:
                        print(f"   📊 Average NDVI: {trend_summary['avg_ndvi']:.3f}")
    
    def demo_monitoring_locations(self):
        """Show all monitoring locations"""
        self.print_header("MONITORING NETWORK")
        
        print(f"\n🌐 AgentWeaver monitors {len(self.pipeline.monitoring_locations)} key agricultural locations across India:")
        
        for i, location in enumerate(self.pipeline.monitoring_locations, 1):
            print(f"   {i:2d}. {location.location_name}, {location.region}")
            print(f"       📍 {location.latitude:.4f}°N, {location.longitude:.4f}°E")
            if location.elevation:
                print(f"       ⛰️ Elevation: {location.elevation}m")
        
        print(f"\n🎯 This network provides comprehensive coverage of India's diverse agricultural zones!")
    
    async def demo_bulk_acquisition(self):
        """Demonstrate bulk data acquisition"""
        self.print_header("BULK DATA ACQUISITION")
        
        print("\n🚀 Demonstrating bulk satellite data acquisition...")
        print("   This simulates acquiring historical data for research and analysis.")
        
        # Temporarily use fewer locations for demo
        original_locations = self.pipeline.monitoring_locations
        self.pipeline.monitoring_locations = self.demo_locations[:2]  # Use only 2 locations
        
        try:
            print(f"\n📡 Starting bulk acquisition for {len(self.pipeline.monitoring_locations)} locations (7 days)...")
            
            results = await self.pipeline.bulk_acquire_data(days_back=7)
            
            print(f"\n✅ Bulk Acquisition Results:")
            print(f"   📊 Total Data Points: {results['total_data_points']}")
            print(f"   ✅ Successful: {results['successful']}")
            print(f"   ❌ Failed: {results['failed']}")
            
            print(f"\n📍 Location Results:")
            for loc_result in results['locations']:
                status_emoji = "✅" if loc_result['status'] == 'success' else "❌"
                print(f"   {status_emoji} {loc_result['location']}: {loc_result['data_points']} data points")
                if loc_result['latest_ndvi']:
                    print(f"      🌱 Latest NDVI: {loc_result['latest_ndvi']:.3f}")
            
        finally:
            # Restore original locations
            self.pipeline.monitoring_locations = original_locations
    
    def demo_data_quality_assessment(self):
        """Demonstrate data quality assessment"""
        self.print_header("DATA QUALITY ASSESSMENT")
        
        print("\n🔍 Satellite data quality varies based on several factors:")
        print("\n📊 Quality Factors:")
        print("   ☁️ Cloud Cover: Lower is better for optical satellites")
        print("   🎯 Confidence Score: Based on atmospheric conditions and data processing")
        print("   📡 Source Quality: Different satellites have varying precision")
        print("   🌍 Geographic Coverage: Some regions have better satellite coverage")
        
        # Show quality examples
        print("\n📈 Quality Categories:")
        quality_examples = [
            ("Excellent", 0.95, "Clear skies, optimal conditions"),
            ("Good", 0.85, "Minimal cloud cover, good visibility"),
            ("Fair", 0.70, "Moderate clouds, acceptable data"),
            ("Poor", 0.55, "Heavy clouds, limited visibility")
        ]
        
        for quality, confidence, description in quality_examples:
            stars = "⭐" * int(confidence * 5)
            print(f"   {quality:10s} {stars:10s} (≥{confidence:.2f}) - {description}")
    
    async def run_complete_demo(self):
        """Run the complete satellite system demonstration"""
        print("🛰️ AGENTWEAVER SATELLITE DATA ACQUISITION SYSTEM")
        print("🌾 Advanced Agricultural Intelligence Platform")
        print("=" * 70)
        print("   🚀 Real-time satellite monitoring")
        print("   📊 Historical data simulation")
        print("   🌍 Multi-location coverage")
        print("   🎯 Agricultural decision support")
        print("=" * 70)
        
        try:
            # Run demonstration modules
            await self.demo_real_time_acquisition()
            await asyncio.sleep(1)
            
            await self.demo_historical_simulation()
            await asyncio.sleep(1)
            
            self.demo_location_analysis()
            await asyncio.sleep(1)
            
            self.demo_monitoring_locations()
            await asyncio.sleep(1)
            
            await self.demo_bulk_acquisition()
            await asyncio.sleep(1)
            
            self.demo_data_quality_assessment()
            
            # Final summary
            self.print_header("DEMONSTRATION COMPLETE")
            print("\n🎉 Satellite Data Acquisition System demonstration completed successfully!")
            print("\n🚀 System Capabilities Demonstrated:")
            print("   ✅ Real-time data acquisition")
            print("   ✅ Historical data simulation")
            print("   ✅ Multi-location monitoring")
            print("   ✅ Bulk data processing")
            print("   ✅ Quality assessment")
            print("   ✅ Agricultural intelligence")
            
            print("\n🌾 Ready for Agricultural Agent Integration!")
            print("   🔗 Crop Selection Agent can use NDVI data")
            print("   🔗 Irrigation Agent can use soil moisture data")
            print("   🔗 Weather patterns support all agents")
            
            print("\n📡 API Endpoints Available:")
            print("   GET  /api/satellite/health - Service health check")
            print("   POST /api/satellite/acquire - Acquire data for location")
            print("   GET  /api/satellite/data - Retrieve location data")
            print("   GET  /api/satellite/locations - List monitoring locations")
            print("   POST /api/satellite/monitoring/start - Start continuous monitoring")
            
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
            print("🔧 Please check system configuration and try again.")

async def main():
    """Main demonstration function"""
    print("Starting Satellite Data Acquisition System Demo...")
    print("Press Ctrl+C to stop at any time.\n")
    
    try:
        demo = SatelliteDemo()
        await demo.run_complete_demo()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user.")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
