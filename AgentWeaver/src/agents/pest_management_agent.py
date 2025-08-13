"""
Pest Management Agent
Specialized agent for pest identification, outbreak forecasting, and treatment recommendations.
Focuses on text-based identification and integrated pest management strategies.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import re

from .base_agent import BaseAgent
from ..core.agriculture_models import (
    AgricultureQuery, AgentResponse, CropType, Season, WeatherData,
    Location, FarmProfile, QueryDomain
)

logger = logging.getLogger(__name__)


class PestType(Enum):
    """Types of agricultural pests"""
    INSECT = "insect"
    DISEASE = "disease"
    WEED = "weed"
    FUNGAL = "fungal"
    VIRAL = "viral"
    BACTERIAL = "bacterial"
    NEMATODE = "nematode"


class SeverityLevel(Enum):
    """Pest infestation severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class TreatmentType(Enum):
    """Types of pest treatments"""
    BIOLOGICAL = "biological"
    CHEMICAL = "chemical"
    CULTURAL = "cultural"
    MECHANICAL = "mechanical"
    INTEGRATED = "integrated"


@dataclass
class PestIdentification:
    """Pest identification result"""
    pest_name: str
    pest_type: PestType
    confidence: float  # 0.0 to 1.0
    symptoms: List[str]
    affected_crops: List[CropType]
    severity_indicators: List[str]
    common_names: List[str]
    description: str


@dataclass
class TreatmentRecommendation:
    """Pest treatment recommendation"""
    treatment_type: TreatmentType
    method: str
    products: List[str]
    application_timing: str
    frequency: str
    dosage: str
    cost_estimate: float  # rupees per hectare
    effectiveness: float  # 0.0 to 1.0
    safety_precautions: List[str]
    environmental_impact: str


@dataclass
class PestForecast:
    """Pest outbreak forecast"""
    pest_name: str
    risk_level: SeverityLevel
    outbreak_probability: float  # 0.0 to 1.0
    peak_activity_period: Tuple[int, int]  # start_week, end_week
    weather_factors: List[str]
    preventive_measures: List[str]


class PestManagementAgent(BaseAgent):
    """
    Agent specialized in pest identification, forecasting, and management.
    
    Capabilities:
    - Pest identification from symptom descriptions
    - Treatment recommendations (biological, chemical, cultural)
    - Outbreak forecasting based on weather and seasonal patterns
    - Integrated pest management strategies
    - Prevention and early detection advice
    """
    
    def __init__(self):
        super().__init__(
            agent_id="pest_management_agent",
            name="Pest Management Specialist",
            description="Expert in pest identification and integrated management strategies",
            capabilities=[
                "pest_identification",
                "treatment_recommendation",
                "outbreak_forecasting",
                "ipm_strategies",
                "prevention_advice"
            ]
        )
        
        # Load pest knowledge base
        self._load_pest_database()
        self._load_treatment_database()
        self._load_forecast_models()
        logger.info(f"Initialized {self.name} with {len(self.pest_database)} pest entries")
    
    def _load_pest_database(self):
        """Load comprehensive pest identification database"""
        self.pest_database = {
            # Wheat Pests
            "wheat_rust": {
                "scientific_name": "Puccinia triticina",
                "pest_type": PestType.FUNGAL,
                "common_names": ["leaf rust", "brown rust", "पत्ती का किट्ट"],
                "affected_crops": [CropType.WHEAT],
                "symptoms": [
                    "orange-brown pustules on leaves",
                    "yellowing of leaves",
                    "premature leaf drop",
                    "reduced grain filling",
                    "rust-colored spores on leaf surface"
                ],
                "severity_indicators": [
                    "pustules covering >50% leaf area = severe",
                    "flag leaf affected = high",
                    "multiple tillers affected = moderate to high"
                ],
                "favorable_conditions": {
                    "temperature": (15, 25),
                    "humidity": (60, 100),
                    "rainfall": "moderate to high"
                },
                "peak_season": [Season.RABI],
                "description": "Fungal disease causing rust-colored pustules on wheat leaves"
            },
            
            "aphids": {
                "scientific_name": "Rhopalosiphum padi",
                "pest_type": PestType.INSECT,
                "common_names": ["wheat aphids", "green bug", "माहू"],
                "affected_crops": [CropType.WHEAT, CropType.RICE, CropType.MAIZE],
                "symptoms": [
                    "small green insects on leaves",
                    "honeydew on plant surface",
                    "yellowing and curling of leaves",
                    "stunted plant growth",
                    "presence of ants on plants"
                ],
                "severity_indicators": [
                    ">5 aphids per tiller = economic threshold",
                    "sticky honeydew visible = moderate",
                    "ant trails present = established infestation"
                ],
                "favorable_conditions": {
                    "temperature": (20, 25),
                    "humidity": (70, 85),
                    "rainfall": "low to moderate"
                },
                "peak_season": [Season.RABI, Season.KHARIF],
                "description": "Small sucking insects that feed on plant sap"
            },
            
            # Rice Pests
            "blast_disease": {
                "scientific_name": "Magnaporthe oryzae",
                "pest_type": PestType.FUNGAL,
                "common_names": ["rice blast", "leaf blast", "धान का ब्लास्ट"],
                "affected_crops": [CropType.RICE],
                "symptoms": [
                    "diamond-shaped lesions on leaves",
                    "brown spots with gray centers",
                    "neck blast on panicles",
                    "node blast on stems",
                    "white/gray fungal growth"
                ],
                "severity_indicators": [
                    "neck blast = severe yield loss",
                    ">20% leaf area affected = high",
                    "multiple nodes affected = severe"
                ],
                "favorable_conditions": {
                    "temperature": (25, 28),
                    "humidity": (85, 95),
                    "rainfall": "high with intermittent dry periods"
                },
                "peak_season": [Season.KHARIF],
                "description": "Devastating fungal disease of rice causing blast lesions"
            },
            
            "stem_borer": {
                "scientific_name": "Scirpophaga incertulas",
                "pest_type": PestType.INSECT,
                "common_names": ["yellow stem borer", "तना छेदक"],
                "affected_crops": [CropType.RICE],
                "symptoms": [
                    "dead hearts in young plants",
                    "white ears in mature plants",
                    "entry holes in stem",
                    "frass near stem base",
                    "easy pulling of central shoot"
                ],
                "severity_indicators": [
                    ">5% dead hearts = economic threshold",
                    "white ears present = severe damage",
                    "multiple tillers affected = high"
                ],
                "favorable_conditions": {
                    "temperature": (26, 32),
                    "humidity": (70, 85),
                    "rainfall": "moderate"
                },
                "peak_season": [Season.KHARIF],
                "description": "Insect pest that bores into rice stems causing dead hearts"
            },
            
            # Cotton Pests
            "bollworm": {
                "scientific_name": "Helicoverpa armigera",
                "pest_type": PestType.INSECT,
                "common_names": ["cotton bollworm", "American bollworm", "कपास का किट्ट"],
                "affected_crops": [CropType.COTTON],
                "symptoms": [
                    "holes in cotton bolls",
                    "caterpillars inside bolls",
                    "damaged flowers and buds",
                    "frass around feeding sites",
                    "premature boll drop"
                ],
                "severity_indicators": [
                    ">2 larvae per plant = economic threshold",
                    "boll damage >10% = high",
                    "multiple bolls affected = severe"
                ],
                "favorable_conditions": {
                    "temperature": (25, 30),
                    "humidity": (60, 80),
                    "rainfall": "moderate"
                },
                "peak_season": [Season.KHARIF],
                "description": "Major insect pest of cotton attacking bolls and flowers"
            },
            
            "whitefly": {
                "scientific_name": "Bemisia tabaci",
                "pest_type": PestType.INSECT,
                "common_names": ["cotton whitefly", "सफ़ेद मक्खी"],
                "affected_crops": [CropType.COTTON, CropType.TOMATO],
                "symptoms": [
                    "small white flying insects",
                    "yellowing of leaves",
                    "honeydew on leaf surface",
                    "sooty mold development",
                    "leaf curling and distortion"
                ],
                "severity_indicators": [
                    ">5 adults per leaf = economic threshold",
                    "yellowing >25% leaves = moderate",
                    "sooty mold present = established"
                ],
                "favorable_conditions": {
                    "temperature": (25, 32),
                    "humidity": (70, 85),
                    "rainfall": "low"
                },
                "peak_season": [Season.KHARIF],
                "description": "Small white insect that transmits viral diseases"
            },
            
            # General Pests
            "cutworm": {
                "scientific_name": "Agrotis ipsilon",
                "pest_type": PestType.INSECT,
                "common_names": ["cutworm", "कटवर्म"],
                "affected_crops": [CropType.WHEAT, CropType.MAIZE, CropType.COTTON],
                "symptoms": [
                    "cut seedlings at soil level",
                    "plants found lying on ground",
                    "smooth cuts near soil surface",
                    "caterpillars hiding in soil during day",
                    "damage during night"
                ],
                "severity_indicators": [
                    ">5% plant cutting = economic threshold",
                    "multiple plants cut = moderate",
                    "field patches affected = high"
                ],
                "favorable_conditions": {
                    "temperature": (18, 25),
                    "humidity": (70, 85),
                    "rainfall": "moderate"
                },
                "peak_season": [Season.RABI, Season.KHARIF],
                "description": "Soil-dwelling caterpillar that cuts young plants at ground level"
            }
        }
    
    def _load_treatment_database(self):
        """Load treatment recommendations database"""
        self.treatment_database = {
            "wheat_rust": [
                {
                    "treatment_type": TreatmentType.CHEMICAL,
                    "method": "Fungicide spray",
                    "products": ["Propiconazole 25% EC", "Tebuconazole 250 EC"],
                    "application_timing": "At first appearance of symptoms",
                    "frequency": "2-3 sprays at 15-day intervals",
                    "dosage": "1ml per liter water",
                    "cost_estimate": 2500,
                    "effectiveness": 0.85,
                    "safety_precautions": [
                        "Use protective equipment",
                        "Avoid spraying during windy conditions",
                        "Do not spray during flowering"
                    ],
                    "environmental_impact": "moderate"
                },
                {
                    "treatment_type": TreatmentType.CULTURAL,
                    "method": "Resistant varieties",
                    "products": ["HD-2967", "PBW-725"],
                    "application_timing": "At sowing time",
                    "frequency": "Every season",
                    "dosage": "Use certified seed",
                    "cost_estimate": 500,
                    "effectiveness": 0.90,
                    "safety_precautions": [],
                    "environmental_impact": "low"
                }
            ],
            
            "aphids": [
                {
                    "treatment_type": TreatmentType.BIOLOGICAL,
                    "method": "Predator release",
                    "products": ["Ladybird beetles", "Chrysoperla carnea"],
                    "application_timing": "Early infestation stage",
                    "frequency": "Release when needed",
                    "dosage": "5000 predators per hectare",
                    "cost_estimate": 1500,
                    "effectiveness": 0.75,
                    "safety_precautions": [],
                    "environmental_impact": "very low"
                },
                {
                    "treatment_type": TreatmentType.CHEMICAL,
                    "method": "Insecticide spray",
                    "products": ["Imidacloprid 17.8% SL", "Acetamiprid 20% SP"],
                    "application_timing": "When threshold reached",
                    "frequency": "1-2 sprays as needed",
                    "dosage": "0.5ml per liter water",
                    "cost_estimate": 1800,
                    "effectiveness": 0.90,
                    "safety_precautions": [
                        "Avoid application during bee activity",
                        "Use recommended dosage only"
                    ],
                    "environmental_impact": "moderate"
                }
            ],
            
            "blast_disease": [
                {
                    "treatment_type": TreatmentType.CHEMICAL,
                    "method": "Fungicide application",
                    "products": ["Tricyclazole 75% WP", "Carbendazim 50% WP"],
                    "application_timing": "Prophylactic at tillering stage",
                    "frequency": "2-3 sprays at 10-day intervals",
                    "dosage": "0.6g per liter water",
                    "cost_estimate": 3000,
                    "effectiveness": 0.80,
                    "safety_precautions": [
                        "Rotate fungicides to prevent resistance",
                        "Spray in evening hours"
                    ],
                    "environmental_impact": "moderate"
                },
                {
                    "treatment_type": TreatmentType.CULTURAL,
                    "method": "Water management",
                    "products": ["Alternate wetting and drying"],
                    "application_timing": "Throughout crop season",
                    "frequency": "Continuous",
                    "dosage": "Maintain 2-3cm water level",
                    "cost_estimate": 0,
                    "effectiveness": 0.60,
                    "safety_precautions": [],
                    "environmental_impact": "very low"
                }
            ],
            
            "bollworm": [
                {
                    "treatment_type": TreatmentType.INTEGRATED,
                    "method": "IPM package",
                    "products": ["Pheromone traps", "NPV", "Bt spray"],
                    "application_timing": "From flower initiation",
                    "frequency": "Weekly monitoring and treatment",
                    "dosage": "As per IPM schedule",
                    "cost_estimate": 4000,
                    "effectiveness": 0.85,
                    "safety_precautions": [
                        "Monitor trap catches weekly",
                        "Use economic threshold levels"
                    ],
                    "environmental_impact": "low"
                },
                {
                    "treatment_type": TreatmentType.BIOLOGICAL,
                    "method": "Biocontrol agents",
                    "products": ["Trichogramma", "NPV", "Bt"],
                    "application_timing": "Early larval stage",
                    "frequency": "Weekly releases",
                    "dosage": "50,000 parasitoids per hectare",
                    "cost_estimate": 2500,
                    "effectiveness": 0.70,
                    "safety_precautions": [],
                    "environmental_impact": "very low"
                }
            ]
        }
    
    def _load_forecast_models(self):
        """Load pest outbreak forecasting models"""
        self.forecast_models = {
            "wheat_rust": {
                "weather_factors": {
                    "temperature": (15, 25),
                    "humidity": 80,
                    "rainfall": "moderate",
                    "wind": "present"
                },
                "seasonal_pattern": {
                    Season.RABI: {
                        "high_risk_weeks": (8, 16),  # January-March
                        "peak_weeks": (12, 14)  # February
                    }
                },
                "early_warning_indicators": [
                    "Temperature 15-25°C for 5+ days",
                    "Relative humidity >80%",
                    "Light rains with sunny intervals",
                    "Reports from neighboring areas"
                ]
            },
            
            "bollworm": {
                "weather_factors": {
                    "temperature": (25, 30),
                    "humidity": 70,
                    "rainfall": "light_to_moderate"
                },
                "seasonal_pattern": {
                    Season.KHARIF: {
                        "high_risk_weeks": (25, 35),  # June-August
                        "peak_weeks": (28, 32)  # July
                    }
                },
                "early_warning_indicators": [
                    "Flower initiation stage reached",
                    "Temperature 25-30°C consistently",
                    "Adult moth trap catches increasing",
                    "Previous season infestation history"
                ]
            }
        }
    
    async def process_query(self, query: AgricultureQuery) -> AgentResponse:
        """
        Process pest management related queries.
        
        Args:
            query: Agriculture query object
            
        Returns:
            AgentResponse with pest identification and treatment recommendations
        """
        try:
            logger.info(f"Processing pest management query: {query.query_text}")
            
            # Extract pest-related information from query
            context = self._extract_pest_context(query)
            
            # Identify pest based on symptoms
            pest_identifications = await self._identify_pest(context)
            
            # Generate treatment recommendations
            treatments = await self._recommend_treatments(pest_identifications, context)
            
            # Generate outbreak forecast if applicable
            forecasts = await self._generate_pest_forecast(context)
            
            # Calculate confidence
            confidence = self._calculate_confidence(context, pest_identifications)
            
            # Format response
            response_data = {
                "pest_identifications": [pest.__dict__ for pest in pest_identifications],
                "treatment_recommendations": [treatment.__dict__ for treatment in treatments],
                "outbreak_forecasts": [forecast.__dict__ for forecast in forecasts],
                "context_analysis": context,
                "confidence_score": confidence,
                "prevention_advice": self._generate_prevention_advice(context)
            }
            
            return AgentResponse(
                agent_id=self.agent_id,
                query_id=query.query_id,
                status="completed",
                response=response_data,
                confidence=confidence,
                processing_time=0.0,
                sources=["pest_database", "treatment_database", "ipm_guidelines"],
                recommendations=self._format_pest_summary(pest_identifications, treatments)
            )
            
        except Exception as e:
            logger.error(f"Error processing pest management query: {e}")
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
    
    def _extract_pest_context(self, query: AgricultureQuery) -> Dict[str, Any]:
        """Extract pest-related context from query"""
        context = {
            "symptoms": [],
            "crop_type": None,
            "affected_parts": [],
            "severity": None,
            "timing": None,
            "weather_conditions": None,
            "location": None,
            "query_type": "identification"  # identification, treatment, forecast
        }
        
        query_text = query.query_text.lower()
        
        # Extract crop information
        for crop_type in CropType:
            crop_names = [crop_type.value, crop_type.name.lower()]
            hindi_names = {
                CropType.WHEAT: ["gehu", "gehun"],
                CropType.RICE: ["chawal", "dhan"],
                CropType.COTTON: ["kapas"],
                CropType.MAIZE: ["makka"]
            }
            if crop_type in hindi_names:
                crop_names.extend(hindi_names[crop_type])
            
            if any(name in query_text for name in crop_names):
                context["crop_type"] = crop_type
                break
        
        # Extract symptoms
        symptom_keywords = {
            "spots": "spotted lesions",
            "yellow": "yellowing",
            "brown": "browning",
            "holes": "holes in leaves/fruits",
            "insects": "insect presence",
            "rust": "rust-colored pustules",
            "wilting": "plant wilting",
            "stunted": "stunted growth",
            "holes": "feeding holes",
            "sticky": "honeydew presence"
        }
        
        for keyword, symptom in symptom_keywords.items():
            if keyword in query_text:
                context["symptoms"].append(symptom)
        
        # Extract affected plant parts
        part_keywords = ["leaves", "stem", "fruit", "flower", "root", "boll"]
        for part in part_keywords:
            if part in query_text:
                context["affected_parts"].append(part)
        
        # Determine query type
        if any(word in query_text for word in ["spray", "treatment", "control", "manage"]):
            context["query_type"] = "treatment"
        elif any(word in query_text for word in ["forecast", "predict", "when", "outbreak"]):
            context["query_type"] = "forecast"
        
        # Extract location if available
        if query.farm_profile and query.farm_profile.location:
            context["location"] = query.farm_profile.location
        
        return context
    
    async def _identify_pest(self, context: Dict[str, Any]) -> List[PestIdentification]:
        """Identify pests based on symptoms and context"""
        identifications = []
        
        for pest_name, pest_data in self.pest_database.items():
            confidence = self._calculate_pest_match_confidence(pest_data, context)
            
            if confidence > 0.3:  # Include reasonably confident matches
                identification = PestIdentification(
                    pest_name=pest_name,
                    pest_type=pest_data["pest_type"],
                    confidence=confidence,
                    symptoms=pest_data["symptoms"],
                    affected_crops=pest_data["affected_crops"],
                    severity_indicators=pest_data["severity_indicators"],
                    common_names=pest_data["common_names"],
                    description=pest_data["description"]
                )
                identifications.append(identification)
        
        # Sort by confidence
        identifications.sort(key=lambda x: x.confidence, reverse=True)
        
        return identifications[:3]  # Return top 3 matches
    
    def _calculate_pest_match_confidence(self, pest_data: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate confidence score for pest identification"""
        confidence = 0.0
        
        # Crop match (30% weight)
        if context["crop_type"] and context["crop_type"] in pest_data["affected_crops"]:
            confidence += 0.30
        
        # Symptom match (40% weight)
        if context["symptoms"]:
            symptom_matches = 0
            for user_symptom in context["symptoms"]:
                for pest_symptom in pest_data["symptoms"]:
                    if any(word in pest_symptom.lower() for word in user_symptom.lower().split()):
                        symptom_matches += 1
                        break
            
            symptom_score = min(symptom_matches / len(context["symptoms"]), 1.0)
            confidence += 0.40 * symptom_score
        
        # Plant part match (20% weight)
        if context["affected_parts"]:
            part_matches = 0
            for part in context["affected_parts"]:
                if any(part in symptom.lower() for symptom in pest_data["symptoms"]):
                    part_matches += 1
            
            if part_matches > 0:
                confidence += 0.20
        
        # Seasonal relevance (10% weight)
        current_month = datetime.now().month
        if current_month in [10, 11, 12, 1, 2, 3]:  # Rabi
            current_season = Season.RABI
        else:  # Kharif
            current_season = Season.KHARIF
        
        if current_season in pest_data["peak_season"]:
            confidence += 0.10
        
        return confidence
    
    async def _recommend_treatments(self, pest_identifications: List[PestIdentification], context: Dict[str, Any]) -> List[TreatmentRecommendation]:
        """Generate treatment recommendations for identified pests"""
        treatments = []
        
        for pest_id in pest_identifications[:2]:  # Top 2 pest identifications
            pest_name = pest_id.pest_name
            
            if pest_name in self.treatment_database:
                pest_treatments = self.treatment_database[pest_name]
                
                for treatment_data in pest_treatments:
                    treatment = TreatmentRecommendation(
                        treatment_type=treatment_data["treatment_type"],
                        method=treatment_data["method"],
                        products=treatment_data["products"],
                        application_timing=treatment_data["application_timing"],
                        frequency=treatment_data["frequency"],
                        dosage=treatment_data["dosage"],
                        cost_estimate=treatment_data["cost_estimate"],
                        effectiveness=treatment_data["effectiveness"],
                        safety_precautions=treatment_data["safety_precautions"],
                        environmental_impact=treatment_data["environmental_impact"]
                    )
                    treatments.append(treatment)
        
        # Sort by effectiveness and environmental friendliness
        treatments.sort(key=lambda x: (x.effectiveness, -0.1 if x.environmental_impact == "low" else 0), reverse=True)
        
        return treatments[:4]  # Return top 4 treatments
    
    async def _generate_pest_forecast(self, context: Dict[str, Any]) -> List[PestForecast]:
        """Generate pest outbreak forecasts"""
        forecasts = []
        
        if context["query_type"] == "forecast" or context["crop_type"]:
            current_week = datetime.now().isocalendar()[1]
            
            for pest_name, forecast_data in self.forecast_models.items():
                # Check if pest is relevant to current crop
                if context["crop_type"]:
                    pest_data = self.pest_database.get(pest_name, {})
                    if context["crop_type"] not in pest_data.get("affected_crops", []):
                        continue
                
                # Calculate risk based on seasonal patterns
                risk_level = self._calculate_outbreak_risk(forecast_data, current_week)
                
                if risk_level.value != "low":  # Only include moderate+ risks
                    forecast = PestForecast(
                        pest_name=pest_name,
                        risk_level=risk_level,
                        outbreak_probability=self._calculate_outbreak_probability(forecast_data, current_week),
                        peak_activity_period=forecast_data["seasonal_pattern"][Season.RABI]["peak_weeks"],
                        weather_factors=forecast_data["early_warning_indicators"],
                        preventive_measures=self._get_preventive_measures(pest_name)
                    )
                    forecasts.append(forecast)
        
        return forecasts
    
    def _calculate_outbreak_risk(self, forecast_data: Dict[str, Any], current_week: int) -> SeverityLevel:
        """Calculate outbreak risk level"""
        # This is a simplified model - in production would use weather data
        for season, pattern in forecast_data["seasonal_pattern"].items():
            high_risk_start, high_risk_end = pattern["high_risk_weeks"]
            
            if high_risk_start <= current_week <= high_risk_end:
                return SeverityLevel.HIGH
            elif abs(current_week - high_risk_start) <= 2 or abs(current_week - high_risk_end) <= 2:
                return SeverityLevel.MODERATE
        
        return SeverityLevel.LOW
    
    def _calculate_outbreak_probability(self, forecast_data: Dict[str, Any], current_week: int) -> float:
        """Calculate probability of pest outbreak"""
        # Simplified calculation based on seasonal patterns
        for season, pattern in forecast_data["seasonal_pattern"].items():
            peak_start, peak_end = pattern["peak_weeks"]
            
            if peak_start <= current_week <= peak_end:
                return 0.8
            elif abs(current_week - peak_start) <= 2:
                return 0.6
            elif abs(current_week - peak_end) <= 2:
                return 0.5
        
        return 0.2
    
    def _get_preventive_measures(self, pest_name: str) -> List[str]:
        """Get preventive measures for specific pest"""
        prevention_measures = {
            "wheat_rust": [
                "Use resistant varieties",
                "Avoid excessive nitrogen fertilization", 
                "Ensure proper air circulation",
                "Remove crop residues"
            ],
            "aphids": [
                "Monitor regularly with yellow sticky traps",
                "Encourage natural predators",
                "Avoid excessive nitrogen fertilization",
                "Use reflective mulch"
            ],
            "bollworm": [
                "Install pheromone traps",
                "Maintain trap crops",
                "Regular field monitoring",
                "Destroy crop residues"
            ]
        }
        
        return prevention_measures.get(pest_name, [
            "Regular field monitoring",
            "Maintain field hygiene",
            "Use healthy seeds",
            "Proper crop rotation"
        ])
    
    def _calculate_confidence(self, context: Dict[str, Any], identifications: List[PestIdentification]) -> float:
        """Calculate confidence in pest management recommendations"""
        confidence = 0.4  # Base confidence
        
        # Symptom detail availability
        if len(context["symptoms"]) >= 2:
            confidence += 0.20
        elif len(context["symptoms"]) >= 1:
            confidence += 0.10
        
        # Crop information available
        if context["crop_type"]:
            confidence += 0.15
        
        # Plant part information
        if context["affected_parts"]:
            confidence += 0.10
        
        # Identification quality
        if identifications and identifications[0].confidence > 0.7:
            confidence += 0.15
        
        return min(confidence, 0.90)
    
    def _generate_prevention_advice(self, context: Dict[str, Any]) -> List[str]:
        """Generate general prevention advice"""
        advice = [
            "Conduct regular field inspections (2-3 times per week)",
            "Maintain proper crop rotation to break pest cycles",
            "Use certified and treated seeds",
            "Ensure balanced fertilization - avoid excess nitrogen",
            "Maintain field hygiene by removing crop residues",
            "Encourage beneficial insects with flowering borders",
            "Install monitoring traps early in the season",
            "Keep records of pest occurrences for future planning"
        ]
        
        # Add crop-specific advice
        if context["crop_type"] == CropType.WHEAT:
            advice.extend([
                "Use rust-resistant wheat varieties in your area",
                "Avoid late sowing to reduce aphid pressure"
            ])
        elif context["crop_type"] == CropType.COTTON:
            advice.extend([
                "Use Bt cotton varieties for bollworm management",
                "Maintain refuge area as per guidelines"
            ])
        
        return advice
    
    def _format_pest_summary(self, identifications: List[PestIdentification], treatments: List[TreatmentRecommendation]) -> List[str]:
        """Format pest management summary"""
        summary = []
        
        if identifications:
            top_pest = identifications[0]
            summary.append(f"Most likely pest: {top_pest.pest_name} ({top_pest.confidence:.1%} confidence)")
        
        if treatments:
            top_treatment = treatments[0]
            summary.append(f"Recommended treatment: {top_treatment.method} (₹{top_treatment.cost_estimate:,}/hectare)")
        
        return summary
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "Pest identification from symptom descriptions",
            "Treatment recommendations (biological, chemical, cultural)",
            "Integrated pest management strategies",
            "Outbreak forecasting and risk assessment",
            "Prevention and early detection advice",
            "Economic threshold guidance"
        ]
    
    def get_supported_queries(self) -> List[str]:
        """Return examples of supported query types"""
        return [
            "My wheat has yellow spots, what could it be?",
            "How to control aphids in rice crop?",
            "When is bollworm season in cotton?",
            "Best spray for rust in wheat",
            "Organic pest control methods",
            "Early signs of stem borer in rice"
        ]
