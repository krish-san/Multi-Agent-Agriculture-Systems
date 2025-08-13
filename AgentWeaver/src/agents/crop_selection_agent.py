"""
Crop Selection Agent
Specialized agent for recommending optimal crop varieties based on location, soil, and weather conditions.
Provides yield predictions and cultivation advice.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .base_agent import BaseAgent
from ..core.agriculture_models import (
    AgricultureQuery, AgentResponse, CropType, SoilType, Season, 
    WeatherData, Location, FarmProfile, QueryDomain
)

logger = logging.getLogger(__name__)


@dataclass
class CropRecommendation:
    """Individual crop recommendation with details"""
    crop_type: CropType
    variety: str
    suitability_score: float  # 0.0 to 1.0
    expected_yield: float  # kg/hectare
    cultivation_period: int  # days
    water_requirement: float  # mm/season
    investment_cost: float  # rupees/hectare
    market_demand: str  # high, medium, low
    risk_factors: List[str]
    cultivation_tips: List[str]
    reason: str  # Why this crop is recommended


@dataclass
class SeasonalCropData:
    """Seasonal crop cultivation data"""
    season: Season
    suitable_crops: List[CropType]
    planting_window: Tuple[int, int]  # month numbers (1-12)
    harvest_window: Tuple[int, int]  # month numbers (1-12)
    weather_requirements: Dict[str, Any]


class CropSelectionAgent(BaseAgent):
    """
    Agent specialized in crop selection and yield prediction.
    
    Capabilities:
    - Crop variety recommendations based on soil, weather, location
    - Seasonal crop planning
    - Yield estimation
    - Risk assessment
    - Cultivation guidance
    """
    
    def __init__(self):
        super().__init__(
            agent_id="crop_selection_agent",
            name="Crop Selection Specialist",
            description="Expert in crop variety selection and cultivation planning",
            capabilities=[
                "crop_recommendation",
                "yield_prediction", 
                "seasonal_planning",
                "soil_suitability_analysis",
                "variety_comparison"
            ]
        )
        
        # Load crop knowledge base
        self._load_crop_database()
        self._load_regional_data()
        logger.info(f"Initialized {self.name} with {len(self.crop_database)} crop varieties")
    
    def _load_crop_database(self):
        """Load comprehensive crop database with varieties and requirements"""
        self.crop_database = {
            CropType.WHEAT: {
                "varieties": {
                    "HD-2967": {
                        "yield_potential": 4500,  # kg/hectare
                        "duration": 145,  # days
                        "soil_preference": [SoilType.LOAMY, SoilType.CLAY_LOAM],
                        "water_requirement": 450,  # mm
                        "temperature_range": (15, 25),  # celsius
                        "rainfall_range": (300, 600),  # mm
                        "resistance": ["rust", "drought_tolerant"],
                        "market_demand": "high",
                        "investment_cost": 25000
                    },
                    "PBW-343": {
                        "yield_potential": 4200,
                        "duration": 140,
                        "soil_preference": [SoilType.LOAMY, SoilType.SANDY_LOAM],
                        "water_requirement": 420,
                        "temperature_range": (12, 22),
                        "rainfall_range": (250, 500),
                        "resistance": ["yellow_rust"],
                        "market_demand": "high",
                        "investment_cost": 23000
                    },
                    "DBW-88": {
                        "yield_potential": 4800,
                        "duration": 150,
                        "soil_preference": [SoilType.CLAY_LOAM, SoilType.CLAY],
                        "water_requirement": 480,
                        "temperature_range": (14, 24),
                        "rainfall_range": (350, 650),
                        "resistance": ["brown_rust", "high_fertility_responsive"],
                        "market_demand": "high",
                        "investment_cost": 27000
                    }
                },
                "seasons": [Season.RABI],
                "planting_months": [10, 11, 12],
                "harvest_months": [3, 4, 5]
            },
            
            CropType.RICE: {
                "varieties": {
                    "Basmati-370": {
                        "yield_potential": 3500,
                        "duration": 140,
                        "soil_preference": [SoilType.CLAY_LOAM, SoilType.CLAY],
                        "water_requirement": 1200,
                        "temperature_range": (20, 30),
                        "rainfall_range": (800, 1500),
                        "resistance": ["blast_resistant"],
                        "market_demand": "very_high",
                        "investment_cost": 35000
                    },
                    "PR-126": {
                        "yield_potential": 6000,
                        "duration": 145,
                        "soil_preference": [SoilType.CLAY_LOAM, SoilType.LOAMY],
                        "water_requirement": 1350,
                        "temperature_range": (22, 32),
                        "rainfall_range": (900, 1600),
                        "resistance": ["bacterial_blight", "high_yielding"],
                        "market_demand": "high",
                        "investment_cost": 40000
                    },
                    "Pusa-44": {
                        "yield_potential": 5500,
                        "duration": 160,
                        "soil_preference": [SoilType.CLAY, SoilType.CLAY_LOAM],
                        "water_requirement": 1400,
                        "temperature_range": (25, 35),
                        "rainfall_range": (1000, 1800),
                        "resistance": ["stem_borer", "leaf_folder"],
                        "market_demand": "medium",
                        "investment_cost": 38000
                    }
                },
                "seasons": [Season.KHARIF, Season.RABI],
                "planting_months": [5, 6, 7, 11, 12],
                "harvest_months": [9, 10, 11, 3, 4]
            },
            
            CropType.COTTON: {
                "varieties": {
                    "Bt-Cotton-RCH-659": {
                        "yield_potential": 2800,
                        "duration": 180,
                        "soil_preference": [SoilType.SANDY_LOAM, SoilType.LOAMY],
                        "water_requirement": 700,
                        "temperature_range": (25, 35),
                        "rainfall_range": (500, 1000),
                        "resistance": ["bollworm_resistant", "drought_tolerant"],
                        "market_demand": "high",
                        "investment_cost": 45000
                    },
                    "Hybrid-6": {
                        "yield_potential": 3200,
                        "duration": 190,
                        "soil_preference": [SoilType.LOAMY, SoilType.CLAY_LOAM],
                        "water_requirement": 750,
                        "temperature_range": (22, 32),
                        "rainfall_range": (600, 1200),
                        "resistance": ["pink_bollworm", "high_fiber_quality"],
                        "market_demand": "very_high",
                        "investment_cost": 50000
                    }
                },
                "seasons": [Season.KHARIF],
                "planting_months": [4, 5, 6],
                "harvest_months": [10, 11, 12]
            },
            
            CropType.SUGARCANE: {
                "varieties": {
                    "Co-86032": {
                        "yield_potential": 85000,  # kg/hectare
                        "duration": 365,  # days
                        "soil_preference": [SoilType.LOAMY, SoilType.CLAY_LOAM],
                        "water_requirement": 1500,
                        "temperature_range": (20, 30),
                        "rainfall_range": (1000, 1500),
                        "resistance": ["red_rot", "smut"],
                        "market_demand": "medium",
                        "investment_cost": 60000
                    },
                    "CoS-767": {
                        "yield_potential": 90000,
                        "duration": 360,
                        "soil_preference": [SoilType.CLAY_LOAM, SoilType.CLAY],
                        "water_requirement": 1600,
                        "temperature_range": (22, 32),
                        "rainfall_range": (1200, 1800),
                        "resistance": ["early_maturity", "high_sugar_content"],
                        "market_demand": "high",
                        "investment_cost": 65000
                    }
                },
                "seasons": [Season.PERENNIAL],
                "planting_months": [2, 3, 9, 10],
                "harvest_months": [12, 1, 2, 3]
            },
            
            CropType.MAIZE: {
                "varieties": {
                    "PMH-1": {
                        "yield_potential": 8000,
                        "duration": 90,
                        "soil_preference": [SoilType.LOAMY, SoilType.SANDY_LOAM],
                        "water_requirement": 400,
                        "temperature_range": (18, 28),
                        "rainfall_range": (300, 700),
                        "resistance": ["early_maturity", "drought_tolerant"],
                        "market_demand": "high",
                        "investment_cost": 20000
                    },
                    "HQPM-1": {
                        "yield_potential": 7500,
                        "duration": 95,
                        "soil_preference": [SoilType.LOAMY, SoilType.CLAY_LOAM],
                        "water_requirement": 450,
                        "temperature_range": (20, 30),
                        "rainfall_range": (400, 800),
                        "resistance": ["quality_protein", "stem_borer_tolerant"],
                        "market_demand": "medium",
                        "investment_cost": 22000
                    }
                },
                "seasons": [Season.KHARIF, Season.RABI],
                "planting_months": [6, 7, 11, 12],
                "harvest_months": [9, 10, 2, 3]
            }
        }
    
    def _load_regional_data(self):
        """Load regional crop suitability and climate data"""
        self.regional_data = {
            "Punjab": {
                "major_crops": [CropType.WHEAT, CropType.RICE, CropType.MAIZE],
                "soil_types": [SoilType.LOAMY, SoilType.CLAY_LOAM],
                "climate": "subtropical",
                "rainfall_average": 650,  # mm
                "temperature_range": (5, 45),
                "irrigation_availability": "high",
                "market_access": "excellent"
            },
            "Rajasthan": {
                "major_crops": [CropType.WHEAT, CropType.MUSTARD, CropType.COTTON],
                "soil_types": [SoilType.SANDY, SoilType.SANDY_LOAM],
                "climate": "arid",
                "rainfall_average": 300,
                "temperature_range": (0, 50),
                "irrigation_availability": "limited",
                "market_access": "good"
            },
            "Maharashtra": {
                "major_crops": [CropType.COTTON, CropType.SUGARCANE, CropType.RICE],
                "soil_types": [SoilType.CLAY, SoilType.CLAY_LOAM, SoilType.SANDY_LOAM],
                "climate": "tropical",
                "rainfall_average": 1200,
                "temperature_range": (10, 42),
                "irrigation_availability": "medium",
                "market_access": "excellent"
            },
            "Uttar Pradesh": {
                "major_crops": [CropType.WHEAT, CropType.RICE, CropType.SUGARCANE],
                "soil_types": [SoilType.LOAMY, SoilType.CLAY_LOAM],
                "climate": "subtropical",
                "rainfall_average": 800,
                "temperature_range": (2, 46),
                "irrigation_availability": "good",
                "market_access": "good"
            }
        }
    
    async def process_query(self, query: AgricultureQuery) -> AgentResponse:
        """
        Process crop selection related queries.
        
        Args:
            query: Agriculture query object
            
        Returns:
            AgentResponse with crop recommendations
        """
        try:
            logger.info(f"Processing crop selection query: {query.query_text}")
            
            # Extract key information from query
            context = self._extract_context_from_query(query)
            
            # Generate crop recommendations
            recommendations = await self._generate_crop_recommendations(context)
            
            # Calculate confidence based on available data
            confidence = self._calculate_confidence(context, recommendations)
            
            # Format response
            response_data = {
                "recommendations": [rec.__dict__ for rec in recommendations],
                "context_analysis": context,
                "confidence_score": confidence,
                "additional_advice": self._generate_additional_advice(context, recommendations)
            }
            
            return AgentResponse(
                agent_id=self.agent_id,
                query_id=query.query_id,
                status="completed",
                response=response_data,
                confidence=confidence,
                processing_time=0.0,  # Will be calculated by caller
                sources=["crop_database", "regional_data", "agricultural_research"],
                recommendations=self._format_recommendations_summary(recommendations)
            )
            
        except Exception as e:
            logger.error(f"Error processing crop selection query: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                query_id=query.query_id,
                status="error",
                response={"error": str(e)},
                confidence=0.0,
                processing_time=0.0,
                sources=[],
                recommendations=[]
            )
    
    def _extract_context_from_query(self, query: AgricultureQuery) -> Dict[str, Any]:
        """Extract relevant context from the query"""
        context = {
            "location": None,
            "season": None,
            "soil_type": None,
            "farm_size": None,
            "budget": None,
            "specific_crop": None,
            "weather_conditions": None,
            "irrigation_available": None,
            "experience_level": "intermediate"
        }
        
        # Extract from farm profile if available
        if query.farm_profile:
            context["location"] = query.farm_profile.location
            context["soil_type"] = query.farm_profile.soil_type
            context["farm_size"] = query.farm_profile.farm_size
            context["irrigation_available"] = query.farm_profile.irrigation_available
        
        # Extract from query text using keyword matching
        query_text = query.query_text.lower()
        
        # Season detection
        if any(word in query_text for word in ["rabi", "winter", "december", "january", "february"]):
            context["season"] = Season.RABI
        elif any(word in query_text for word in ["kharif", "monsoon", "june", "july", "august"]):
            context["season"] = Season.KHARIF
        elif any(word in query_text for word in ["zaid", "summer", "march", "april", "may"]):
            context["season"] = Season.ZAID
        
        # Location detection
        for state in self.regional_data.keys():
            if state.lower() in query_text:
                context["location"] = state
                break
        
        # Crop type detection
        for crop_type in CropType:
            crop_names = [crop_type.value, crop_type.name.lower()]
            # Add common Hindi names
            hindi_names = {
                CropType.WHEAT: ["gehu", "gehun"],
                CropType.RICE: ["chawal", "dhan"],
                CropType.COTTON: ["kapas"],
                CropType.SUGARCANE: ["ganna"],
                CropType.MAIZE: ["makka"]
            }
            if crop_type in hindi_names:
                crop_names.extend(hindi_names[crop_type])
            
            if any(name in query_text for name in crop_names):
                context["specific_crop"] = crop_type
                break
        
        # Soil type detection
        soil_keywords = {
            "sandy": SoilType.SANDY,
            "clay": SoilType.CLAY, 
            "loamy": SoilType.LOAMY,
            "black": SoilType.CLAY,
            "red": SoilType.SANDY_LOAM
        }
        for keyword, soil_type in soil_keywords.items():
            if keyword in query_text:
                context["soil_type"] = soil_type
                break
        
        return context
    
    async def _generate_crop_recommendations(self, context: Dict[str, Any]) -> List[CropRecommendation]:
        """Generate crop recommendations based on context"""
        recommendations = []
        
        # Determine current season if not specified
        current_month = datetime.now().month
        if not context["season"]:
            if current_month in [10, 11, 12, 1, 2, 3]:
                context["season"] = Season.RABI
            elif current_month in [4, 5, 6, 7, 8, 9]:
                context["season"] = Season.KHARIF
        
        # If specific crop requested, focus on that
        if context["specific_crop"]:
            crop_recommendations = self._analyze_specific_crop(
                context["specific_crop"], context
            )
            recommendations.extend(crop_recommendations)
        else:
            # General recommendations based on season and location
            for crop_type, crop_data in self.crop_database.items():
                if context["season"] in crop_data["seasons"]:
                    crop_recommendations = self._analyze_specific_crop(crop_type, context)
                    recommendations.extend(crop_recommendations)
        
        # Sort by suitability score
        recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
        
        # Return top 5 recommendations
        return recommendations[:5]
    
    def _analyze_specific_crop(self, crop_type: CropType, context: Dict[str, Any]) -> List[CropRecommendation]:
        """Analyze suitability of a specific crop type"""
        recommendations = []
        
        if crop_type not in self.crop_database:
            return recommendations
        
        crop_data = self.crop_database[crop_type]
        
        for variety_name, variety_data in crop_data["varieties"].items():
            suitability_score = self._calculate_suitability_score(
                variety_data, context
            )
            
            if suitability_score > 0.3:  # Only include reasonably suitable crops
                recommendation = CropRecommendation(
                    crop_type=crop_type,
                    variety=variety_name,
                    suitability_score=suitability_score,
                    expected_yield=variety_data["yield_potential"] * suitability_score,
                    cultivation_period=variety_data["duration"],
                    water_requirement=variety_data["water_requirement"],
                    investment_cost=variety_data["investment_cost"],
                    market_demand=variety_data["market_demand"],
                    risk_factors=self._identify_risk_factors(variety_data, context),
                    cultivation_tips=self._generate_cultivation_tips(variety_data, context),
                    reason=self._generate_recommendation_reason(variety_data, context, suitability_score)
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_suitability_score(self, variety_data: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate suitability score for a crop variety"""
        score = 0.5  # Base score
        factors = []
        
        # Soil suitability (25% weight)
        if context["soil_type"] and context["soil_type"] in variety_data["soil_preference"]:
            score += 0.25
            factors.append("soil_match")
        elif context["soil_type"]:
            score += 0.1  # Partial match
        
        # Regional suitability (20% weight)
        if context["location"] and context["location"] in self.regional_data:
            regional_info = self.regional_data[context["location"]]
            if variety_data.get("market_demand") == "high" and context["location"] in ["Punjab", "Maharashtra"]:
                score += 0.15
            score += 0.05  # Base regional bonus
            factors.append("regional_suitable")
        
        # Climate suitability (20% weight)
        if context["location"] and context["location"] in self.regional_data:
            regional_info = self.regional_data[context["location"]]
            temp_range = variety_data["temperature_range"]
            regional_temp = regional_info["temperature_range"]
            
            # Check temperature compatibility
            if (temp_range[0] <= regional_temp[1] and temp_range[1] >= regional_temp[0]):
                score += 0.15
                factors.append("climate_suitable")
        
        # Water availability (15% weight)
        if context["irrigation_available"]:
            if variety_data["water_requirement"] > 800 and context["irrigation_available"]:
                score += 0.15
            elif variety_data["water_requirement"] <= 500:  # Drought tolerant
                score += 0.10
            factors.append("water_suitable")
        
        # Market demand (10% weight)
        market_scores = {"very_high": 0.10, "high": 0.08, "medium": 0.05, "low": 0.02}
        score += market_scores.get(variety_data["market_demand"], 0.02)
        
        # Resistance/tolerance (10% weight)
        if "drought_tolerant" in variety_data.get("resistance", []):
            score += 0.05
        if "disease_resistant" in str(variety_data.get("resistance", [])).lower():
            score += 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _identify_risk_factors(self, variety_data: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Identify potential risk factors for the crop"""
        risks = []
        
        # Weather risks
        if variety_data["water_requirement"] > 1000:
            risks.append("High water requirement - drought risk")
        
        # Market risks
        if variety_data["market_demand"] == "low":
            risks.append("Limited market demand")
        
        # Investment risks
        if variety_data["investment_cost"] > 40000:
            risks.append("High initial investment required")
        
        # Duration risks
        if variety_data["duration"] > 150:
            risks.append("Long cultivation period - weather risk")
        
        # Regional risks
        if context["location"] == "Rajasthan" and variety_data["water_requirement"] > 600:
            risks.append("Water scarcity in region")
        
        return risks
    
    def _generate_cultivation_tips(self, variety_data: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate cultivation tips based on variety and context"""
        tips = []
        
        # Soil preparation
        if context["soil_type"] == SoilType.SANDY:
            tips.append("Add organic matter to improve soil water retention")
        elif context["soil_type"] == SoilType.CLAY:
            tips.append("Ensure proper drainage to prevent waterlogging")
        
        # Irrigation
        if variety_data["water_requirement"] > 800:
            tips.append("Install drip irrigation system for water efficiency")
        else:
            tips.append("Monitor soil moisture regularly")
        
        # Fertilization
        tips.append(f"Apply balanced NPK fertilizer as per soil test recommendations")
        
        # Pest management
        if "resistant" in str(variety_data.get("resistance", [])).lower():
            tips.append("Use integrated pest management practices")
        
        # Timing
        tips.append("Plant during optimal weather window for best results")
        
        return tips
    
    def _generate_recommendation_reason(self, variety_data: Dict[str, Any], context: Dict[str, Any], score: float) -> str:
        """Generate explanation for why this crop is recommended"""
        reasons = []
        
        if score > 0.8:
            reasons.append("Excellent match for your conditions")
        elif score > 0.6:
            reasons.append("Good suitability for your farm")
        else:
            reasons.append("Moderate suitability with proper management")
        
        if context["soil_type"] and context["soil_type"] in variety_data["soil_preference"]:
            reasons.append(f"well-suited for {context['soil_type'].value} soil")
        
        if variety_data["market_demand"] in ["high", "very_high"]:
            reasons.append("strong market demand")
        
        if "drought_tolerant" in variety_data.get("resistance", []):
            reasons.append("drought tolerance")
        
        return ", ".join(reasons)
    
    def _calculate_confidence(self, context: Dict[str, Any], recommendations: List[CropRecommendation]) -> float:
        """Calculate confidence score for the recommendations"""
        confidence = 0.5  # Base confidence
        
        # Data availability factors
        if context["location"]:
            confidence += 0.15
        if context["soil_type"]:
            confidence += 0.15
        if context["season"]:
            confidence += 0.10
        if context["farm_size"]:
            confidence += 0.05
        if context["irrigation_available"] is not None:
            confidence += 0.05
        
        # Recommendation quality
        if recommendations and recommendations[0].suitability_score > 0.7:
            confidence += 0.10
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _generate_additional_advice(self, context: Dict[str, Any], recommendations: List[CropRecommendation]) -> List[str]:
        """Generate additional farming advice"""
        advice = []
        
        # Seasonal advice
        current_month = datetime.now().month
        if current_month in [10, 11, 12]:  # Rabi season
            advice.append("Consider crop rotation with legumes to improve soil fertility")
            advice.append("Monitor weather forecasts for frost protection")
        elif current_month in [6, 7, 8]:  # Kharif season
            advice.append("Ensure proper drainage for monsoon season")
            advice.append("Plan for pest management during humid conditions")
        
        # General advice
        advice.append("Get soil testing done before planting for nutrient management")
        advice.append("Consider crop insurance to mitigate weather risks")
        advice.append("Join farmer producer organizations for better market access")
        
        return advice
    
    def _format_recommendations_summary(self, recommendations: List[CropRecommendation]) -> List[str]:
        """Format recommendations for summary display"""
        summary = []
        for rec in recommendations[:3]:  # Top 3 recommendations
            summary.append(
                f"{rec.crop_type.value} ({rec.variety}): "
                f"{rec.suitability_score:.1%} suitable, "
                f"₹{rec.investment_cost:,}/hectare investment"
            )
        return summary
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "Crop variety recommendation based on soil and climate",
            "Yield prediction and profitability analysis", 
            "Seasonal crop planning and rotation advice",
            "Risk assessment and mitigation strategies",
            "Cultivation guidance and best practices",
            "Market demand analysis for crop selection"
        ]
    
    def get_supported_queries(self) -> List[str]:
        """Return examples of supported query types"""
        return [
            "What crop should I grow in [location] during [season]?",
            "Best wheat variety for clay soil",
            "High yield crops for small farms",
            "Drought resistant crops for water scarce areas",
            "Profitable crops with low investment",
            "Crop recommendations for organic farming"
        ]
