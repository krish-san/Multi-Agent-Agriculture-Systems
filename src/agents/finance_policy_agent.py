"""
Finance and Policy Agent
Specialized agent for agricultural loan eligibility, government subsidies, 
and policy recommendations for Indian farmers.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum
import json
import re

from .base_agent import BaseWorkerAgent
from ..core.agriculture_models import (
    AgricultureQuery, AgentResponse, CropType, SoilType, 
    Location, FarmProfile, QueryDomain, Language
)
from .satellite_integration import SatelliteDataIntegrator

logger = logging.getLogger(__name__)


class LoanType(Enum):
    """Types of agricultural loans"""
    CROP_LOAN = "crop_loan"
    FARM_MECHANIZATION = "farm_mechanization"
    LAND_DEVELOPMENT = "land_development"
    IRRIGATION = "irrigation"
    DAIRY = "dairy"
    POULTRY = "poultry"
    HORTICULTURE = "horticulture"
    STORAGE = "storage"
    PROCESSING = "processing"


class SubsidyType(Enum):
    """Types of government subsidies"""
    FERTILIZER = "fertilizer"
    SEED = "seed"
    IRRIGATION_EQUIPMENT = "irrigation_equipment"
    FARM_MACHINERY = "farm_machinery"
    SOLAR_PUMP = "solar_pump"
    CROP_INSURANCE = "crop_insurance"
    ORGANIC_FARMING = "organic_farming"
    SOIL_HEALTH = "soil_health"
    WATERSHED_DEVELOPMENT = "watershed_development"


class IncomeCategory(Enum):
    """Farmer income categories"""
    MARGINAL = "marginal"  # < 1 hectare
    SMALL = "small"        # 1-2 hectares
    SEMI_MEDIUM = "semi_medium"  # 2-4 hectares
    MEDIUM = "medium"      # 4-10 hectares
    LARGE = "large"        # > 10 hectares


@dataclass
class LoanScheme:
    """Agricultural loan scheme details"""
    scheme_name: str
    loan_type: LoanType
    max_amount: float
    interest_rate: float
    tenure_months: int
    eligibility_criteria: List[str]
    required_documents: List[str]
    processing_time_days: int
    collateral_required: bool
    target_beneficiaries: List[str]
    implementing_agency: str
    special_features: List[str]


@dataclass
class SubsidyScheme:
    """Government subsidy scheme details"""
    scheme_name: str
    subsidy_type: SubsidyType
    subsidy_percentage: float
    max_subsidy_amount: float
    eligibility_criteria: List[str]
    required_documents: List[str]
    application_process: List[str]
    implementing_agency: str
    target_beneficiaries: List[str]
    validity_period: str
    special_conditions: List[str]


@dataclass
class EligibilityAssessment:
    """Loan/subsidy eligibility assessment"""
    scheme_name: str
    eligible: bool
    confidence_score: float
    eligibility_percentage: float
    missing_criteria: List[str]
    recommendations: List[str]
    estimated_amount: Optional[float]
    next_steps: List[str]


class FinancePolicyAgent(BaseWorkerAgent):
    """
    Specialized agent for agricultural finance and policy guidance.
    Provides loan eligibility assessment, subsidy recommendations,
    and government scheme information for Indian farmers.
    Enhanced with satellite data for weather risk assessment and yield predictions.
    """
    
    def __init__(self, name: str = "FinancePolicyAgent", capabilities: List = None, agent_type: str = "worker"):
        # Set default capabilities if none provided
        if capabilities is None:
            from ..core.models import AgentCapability
            capabilities = [
                AgentCapability.FINANCE_ANALYSIS,
                AgentCapability.POLICY_GUIDANCE,
                AgentCapability.RISK_ASSESSMENT
            ]
        
        super().__init__(name, capabilities, agent_type)
        
        self.agent_id = "finance_policy_agent"
        self.satellite_integrator = SatelliteDataIntegrator()
        self.finance_capabilities = [
            "loan_eligibility_assessment",
            "subsidy_recommendations", 
            "policy_guidance",
            "documentation_assistance",
            "scheme_comparison",
            "financial_planning",
            "weather_risk_assessment",
            "satellite_enhanced_yield_prediction"
        ]
        
        # Initialize comprehensive scheme databases
        self._initialize_loan_schemes()
        self._initialize_subsidy_schemes()
        self._initialize_policy_knowledge()
    
    def _initialize_loan_schemes(self):
        """Initialize comprehensive agricultural loan schemes database"""
        self.loan_schemes = {
            "kisan_credit_card": LoanScheme(
                scheme_name="Kisan Credit Card (KCC)",
                loan_type=LoanType.CROP_LOAN,
                max_amount=300000.0,  # 3 lakh
                interest_rate=7.0,  # Current rate with subsidy
                tenure_months=12,
                eligibility_criteria=[
                    "Indian citizen",
                    "Age 18-75 years",
                    "Own agricultural land or tenant farmer",
                    "No loan default history",
                    "Valid land documents"
                ],
                required_documents=[
                    "Aadhaar Card", "PAN Card", "Land ownership documents",
                    "Bank account statements", "Passport size photos",
                    "Income certificate", "Crop details"
                ],
                processing_time_days=15,
                collateral_required=False,
                target_beneficiaries=["Small farmers", "Marginal farmers", "Tenant farmers"],
                implementing_agency="All Banks",
                special_features=[
                    "No collateral up to 1.6 lakh",
                    "Interest subvention of 3%",
                    "Flexible repayment",
                    "Multi-year validity"
                ]
            ),
            
            "pm_kisan_mandhan": LoanScheme(
                scheme_name="PM-KISAN Mandhan Yojana",
                loan_type=LoanType.FARM_MECHANIZATION,
                max_amount=200000.0,
                interest_rate=8.5,
                tenure_months=60,
                eligibility_criteria=[
                    "Small and marginal farmers",
                    "Age 18-40 years",
                    "Enrolled in PM-KISAN scheme",
                    "Monthly contribution capacity"
                ],
                required_documents=[
                    "PM-KISAN registration", "Aadhaar Card", "Bank account details",
                    "Land records", "Age proof"
                ],
                processing_time_days=30,
                collateral_required=True,
                target_beneficiaries=["Small farmers", "Marginal farmers"],
                implementing_agency="Ministry of Agriculture",
                special_features=[
                    "Pension scheme linked",
                    "Government contribution matching",
                    "Life insurance coverage"
                ]
            ),
            
            "pmfme_scheme": LoanScheme(
                scheme_name="PM Formalization of Micro Food Processing Enterprises",
                loan_type=LoanType.PROCESSING,
                max_amount=1000000.0,  # 10 lakh
                interest_rate=9.0,
                tenure_months=84,
                eligibility_criteria=[
                    "Existing food processing units",
                    "Annual turnover < 2 crore",
                    "Valid FSSAI license",
                    "Bank account and GST registration"
                ],
                required_documents=[
                    "FSSAI license", "GST certificate", "Bank statements",
                    "Project report", "CA audited financials"
                ],
                processing_time_days=45,
                collateral_required=True,
                target_beneficiaries=["Food processing entrepreneurs", "SHGs", "Cooperatives"],
                implementing_agency="Ministry of Food Processing Industries",
                special_features=[
                    "35% capital subsidy",
                    "Technical support",
                    "Marketing assistance"
                ]
            ),
            
            "nabard_dairy": LoanScheme(
                scheme_name="NABARD Dairy Entrepreneurship Development Scheme",
                loan_type=LoanType.DAIRY,
                max_amount=500000.0,
                interest_rate=8.0,
                tenure_months=72,
                eligibility_criteria=[
                    "Individual farmers or groups",
                    "Experience in animal husbandry",
                    "Technical training completion",
                    "Market linkage availability"
                ],
                required_documents=[
                    "Training certificate", "Project report", "Land documents",
                    "Veterinary clearance", "Bank account proof"
                ],
                processing_time_days=30,
                collateral_required=True,
                target_beneficiaries=["Dairy farmers", "Women entrepreneurs", "Rural youth"],
                implementing_agency="NABARD",
                special_features=[
                    "25% back-ended subsidy",
                    "Technical guidance",
                    "Insurance coverage"
                ]
            )
        }
    
    def _initialize_subsidy_schemes(self):
        """Initialize government subsidy schemes database"""
        self.subsidy_schemes = {
            "pradhan_mantri_krishi_sinchayee": SubsidyScheme(
                scheme_name="Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
                subsidy_type=SubsidyType.IRRIGATION_EQUIPMENT,
                subsidy_percentage=90.0,  # For SC/ST farmers
                max_subsidy_amount=50000.0,
                eligibility_criteria=[
                    "Small and marginal farmers",
                    "Own agricultural land",
                    "Water source availability",
                    "No previous subsidy for same component"
                ],
                required_documents=[
                    "Land ownership documents", "Aadhaar Card", "Bank account details",
                    "Caste certificate (if applicable)", "Water source proof"
                ],
                application_process=[
                    "Apply at Agriculture Department",
                    "Technical verification",
                    "Approval and sanction",
                    "Installation and inspection",
                    "Subsidy disbursement"
                ],
                implementing_agency="Department of Agriculture",
                target_beneficiaries=["Small farmers", "Marginal farmers", "SC/ST farmers"],
                validity_period="Ongoing",
                special_conditions=[
                    "General category: 55% subsidy",
                    "SC/ST/Women: 90% subsidy",
                    "Drip irrigation priority"
                ]
            ),
            
            "sub_mission_agriculture_mechanization": SubsidyScheme(
                scheme_name="Sub Mission on Agricultural Mechanization (SMAM)",
                subsidy_type=SubsidyType.FARM_MACHINERY,
                subsidy_percentage=50.0,
                max_subsidy_amount=125000.0,
                eligibility_criteria=[
                    "Individual farmers",
                    "Farmer groups/cooperatives",
                    "No previous tractor subsidy",
                    "Valid land records"
                ],
                required_documents=[
                    "Land documents", "Aadhaar Card", "Bank account",
                    "Income certificate", "Quotation from dealer"
                ],
                application_process=[
                    "Online application on portal",
                    "Document verification",
                    "Lottery system for selection",
                    "Purchase and claim subsidy"
                ],
                implementing_agency="Department of Agriculture and Cooperation",
                target_beneficiaries=["Small farmers", "Women farmers", "SC/ST farmers"],
                validity_period="Annual budget allocation",
                special_conditions=[
                    "SC/ST: Additional 10% subsidy",
                    "Women: Additional 5% subsidy",
                    "Custom hiring centers priority"
                ]
            ),
            
            "national_mission_organic_farming": SubsidyScheme(
                scheme_name="National Mission on Organic Farming (NMOF)",
                subsidy_type=SubsidyType.ORGANIC_FARMING,
                subsidy_percentage=100.0,
                max_subsidy_amount=25000.0,
                eligibility_criteria=[
                    "Farmers willing to adopt organic farming",
                    "Minimum 2 acres land",
                    "3-year conversion commitment",
                    "Training participation"
                ],
                required_documents=[
                    "Land records", "Aadhaar Card", "Training certificate",
                    "Soil health card", "Bank account details"
                ],
                application_process=[
                    "Register at organic portal",
                    "Attend training program",
                    "Submit land conversion plan",
                    "Get organic certification"
                ],
                implementing_agency="Ministry of Agriculture",
                target_beneficiaries=["Progressive farmers", "SHGs", "FPOs"],
                validity_period="Ongoing with budget allocation",
                special_conditions=[
                    "3-year certification process",
                    "Market linkage support",
                    "Premium price assistance"
                ]
            ),
            
            "pm_kusum_solar": SubsidyScheme(
                scheme_name="PM-KUSUM Solar Pump Scheme",
                subsidy_type=SubsidyType.SOLAR_PUMP,
                subsidy_percentage=60.0,
                max_subsidy_amount=200000.0,
                eligibility_criteria=[
                    "Individual farmers",
                    "Water source availability",
                    "Grid connectivity issues",
                    "Land ownership proof"
                ],
                required_documents=[
                    "Land documents", "Electricity board NOC",
                    "Water source certificate", "Bank account details"
                ],
                application_process=[
                    "Apply at renewable energy agency",
                    "Technical feasibility study",
                    "Vendor selection",
                    "Installation and commissioning"
                ],
                implementing_agency="Ministry of New and Renewable Energy",
                target_beneficiaries=["Farmers in grid-poor areas", "Water stressed regions"],
                validity_period="2023-2026",
                special_conditions=[
                    "30% central subsidy",
                    "30% state subsidy",
                    "40% farmer contribution/loan"
                ]
            )
        }
    
    def _initialize_policy_knowledge(self):
        """Initialize policy and regulatory knowledge base"""
        self.policy_knowledge = {
            "msp_crops": {
                "kharif_2024": {
                    "rice": {"common": 2183, "grade_a": 2203},
                    "wheat": 2275,
                    "maize": 2090,
                    "cotton": 6620,
                    "sugarcane": 340,
                    "soybean": 4892
                },
                "rabi_2024": {
                    "wheat": 2275,
                    "barley": 1735,
                    "gram": 5440,
                    "mustard": 5650
                }
            },
            
            "insurance_schemes": {
                "pmfby": {
                    "name": "Pradhan Mantri Fasal Bima Yojana",
                    "premium_farmer": {"kharif": 2.0, "rabi": 1.5, "commercial": 5.0},
                    "max_claim": "Sum insured",
                    "coverage": "All stages of crop cycle"
                }
            },
            
            "documentation_requirements": {
                "common_documents": [
                    "Aadhaar Card", "PAN Card", "Bank account passbook",
                    "Land ownership documents", "Income certificate"
                ],
                "crop_specific": [
                    "Crop cutting experiment certificate",
                    "Soil health card", "Water analysis report"
                ]
            }
        }
    
    def execute(self, task, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute finance-related tasks with satellite-enhanced analysis"""
        try:
            # Extract query from task
            if hasattr(task, 'query'):
                query = task.query
            elif 'query' in context:
                query = context['query'] 
            else:
                raise ValueError("No query found in task or context")
            
            # Process query using enhanced method
            import asyncio
            if asyncio.get_event_loop().is_running():
                # If already in an async context, create a new task
                future = asyncio.create_task(self.process_query(query))
                response = future.result() if future.done() else None
            else:
                # Run in new event loop
                response = asyncio.run(self.process_query(query))
            
            return {
                'status': 'success',
                'response': response,
                'agent_id': self.agent_id,
                'satellite_enhanced': True
            }
            
        except Exception as e:
            self.logger.error(f"Error executing finance task: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'agent_id': self.agent_id
            }
    
    async def process_query(self, query: AgricultureQuery) -> AgentResponse:
        """Process finance and policy related queries with satellite-enhanced risk assessment"""
        try:
            # Get satellite data for enhanced financial risk assessment
            satellite_data = None
            if query.location and query.location.state:
                try:
                    satellite_data = await self.satellite_integrator.get_satellite_data_for_location(
                        query.location.state, query.location.district or "Default"
                    )
                except Exception as e:
                    self.logger.warning(f"Could not fetch satellite data: {e}")
            
            # Analyze query for finance/policy intent
            query_analysis = self._analyze_finance_query(query.query_text)
            
            # Enhance analysis with satellite insights
            if satellite_data:
                query_analysis["satellite_insights"] = self._analyze_satellite_risk_factors(satellite_data)
            
            # Generate appropriate response based on query type
            if query_analysis["type"] == "loan_eligibility":
                response_data = await self._assess_loan_eligibility(query, query_analysis)
            elif query_analysis["type"] == "subsidy_inquiry":
                response_data = await self._recommend_subsidies(query, query_analysis)
            elif query_analysis["type"] == "policy_information":
                response_data = await self._provide_policy_info(query, query_analysis)
            elif query_analysis["type"] == "documentation_help":
                response_data = await self._assist_documentation(query, query_analysis)
            else:
                response_data = await self._general_finance_guidance(query)
            
            return self._create_agent_response(response_data, query)
            
        except Exception as e:
            logger.error(f"Error processing finance query: {e}")
            return self._create_error_response(query, str(e))
    
    def _analyze_finance_query(self, query_text: str) -> Dict[str, Any]:
        """Analyze query to determine finance/policy intent"""
        query_lower = query_text.lower()
        
        # Loan-related keywords
        loan_keywords = [
            "loan", "लोन", "credit", "क्रेडिट", "kisan credit card", "kcc",
            "बैंक", "bank", "finance", "पैसा", "money", "emi", "interest",
            "ब्याज", "किसान क्रेडिट कार्ड"
        ]
        
        # Subsidy-related keywords  
        subsidy_keywords = [
            "subsidy", "सब्सिडी", "योजना", "scheme", "grant", "अनुदान",
            "प्रधानमंत्री", "pradhan mantri", "government", "सरकार",
            "free", "मुफ्त", "discount", "छूट"
        ]
        
        # Policy/MSP keywords
        policy_keywords = [
            "msp", "minimum support price", "न्यूनतम समर्थन मूल्य",
            "policy", "नीति", "insurance", "बीमा", "pmfby",
            "registration", "पंजीकरण"
        ]
        
        # Documentation keywords
        doc_keywords = [
            "document", "दस्तावेज", "paper", "कागजात", "certificate",
            "प्रमाणपत्र", "aadhaar", "आधार", "application", "आवेदन"
        ]
        
        # Determine query type based on keyword presence
        if any(keyword in query_lower for keyword in loan_keywords):
            query_type = "loan_eligibility"
            extracted_info = self._extract_loan_details(query_text)
        elif any(keyword in query_lower for keyword in subsidy_keywords):
            query_type = "subsidy_inquiry"
            extracted_info = self._extract_subsidy_details(query_text)
        elif any(keyword in query_lower for keyword in policy_keywords):
            query_type = "policy_information"
            extracted_info = self._extract_policy_details(query_text)
        elif any(keyword in query_lower for keyword in doc_keywords):
            query_type = "documentation_help"
            extracted_info = self._extract_documentation_needs(query_text)
        else:
            query_type = "general_finance"
            extracted_info = {}
        
        return {
            "type": query_type,
            "confidence": 0.8,
            "extracted_info": extracted_info,
            "keywords_found": self._get_matching_keywords(query_lower)
        }
    
    def _analyze_satellite_risk_factors(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze satellite data for financial risk assessment"""
        if not satellite_data:
            return {"risk_level": "unknown", "confidence": 0.0}
        
        # Extract key environmental indicators
        ndvi = satellite_data.get('vegetation_health', {}).get('ndvi', 0)
        soil_moisture = satellite_data.get('soil_analysis', {}).get('moisture_percentage', 0)
        temperature = satellite_data.get('weather_conditions', {}).get('temperature', 0)
        humidity = satellite_data.get('weather_conditions', {}).get('humidity', 0)
        
        # Calculate risk scores
        vegetation_risk = self._assess_vegetation_risk(ndvi)
        weather_risk = self._assess_weather_risk(temperature, humidity)
        soil_risk = self._assess_soil_moisture_risk(soil_moisture)
        
        # Overall risk assessment
        overall_risk = (vegetation_risk + weather_risk + soil_risk) / 3
        
        risk_insights = {
            "overall_risk_score": round(overall_risk, 2),
            "risk_level": self._categorize_risk_level(overall_risk),
            "vegetation_health": {"score": ndvi, "risk": vegetation_risk},
            "weather_conditions": {"risk": weather_risk, "temp": temperature, "humidity": humidity},
            "soil_moisture": {"percentage": soil_moisture, "risk": soil_risk},
            "financial_implications": self._generate_financial_implications(overall_risk),
            "recommendations": self._generate_risk_recommendations(overall_risk)
        }
        
        return risk_insights
    
    def _assess_vegetation_risk(self, ndvi: float) -> float:
        """Assess crop risk based on NDVI values"""
        if ndvi >= 0.7:
            return 0.1  # Low risk - healthy vegetation
        elif ndvi >= 0.5:
            return 0.3  # Moderate risk
        elif ndvi >= 0.3:
            return 0.6  # High risk
        else:
            return 0.9  # Very high risk - poor vegetation
    
    def _assess_weather_risk(self, temperature: float, humidity: float) -> float:
        """Assess weather-related financial risk"""
        temp_risk = 0.0
        humidity_risk = 0.0
        
        # Temperature risk assessment
        if temperature > 35 or temperature < 10:
            temp_risk = 0.7  # Extreme temperatures
        elif temperature > 30 or temperature < 15:
            temp_risk = 0.4  # Moderate stress
        else:
            temp_risk = 0.1  # Optimal range
        
        # Humidity risk assessment
        if humidity > 85 or humidity < 30:
            humidity_risk = 0.6  # Disease/drought risk
        elif humidity > 75 or humidity < 40:
            humidity_risk = 0.3  # Moderate risk
        else:
            humidity_risk = 0.1  # Optimal range
        
        return (temp_risk + humidity_risk) / 2
    
    def _assess_soil_moisture_risk(self, moisture: float) -> float:
        """Assess soil moisture risk for crop finance"""
        if moisture >= 60:
            return 0.2  # Good moisture
        elif moisture >= 40:
            return 0.4  # Adequate
        elif moisture >= 20:
            return 0.7  # Dry conditions - higher risk
        else:
            return 0.9  # Very dry - high financial risk
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize overall risk level"""
        if risk_score <= 0.3:
            return "low"
        elif risk_score <= 0.5:
            return "moderate" 
        elif risk_score <= 0.7:
            return "high"
        else:
            return "very_high"
    
    def _generate_financial_implications(self, risk_score: float) -> List[str]:
        """Generate financial implications based on risk score"""
        implications = []
        
        if risk_score <= 0.3:
            implications.extend([
                "Lower insurance premiums likely",
                "Better loan terms possible",
                "Higher yield expectations"
            ])
        elif risk_score <= 0.5:
            implications.extend([
                "Standard insurance coverage recommended",
                "Normal loan terms applicable",
                "Moderate yield expectations"
            ])
        elif risk_score <= 0.7:
            implications.extend([
                "Comprehensive insurance strongly recommended",
                "May require additional collateral",
                "Conservative yield projections advised"
            ])
        else:
            implications.extend([
                "High insurance coverage essential",
                "Loan approval may require extra guarantees",
                "Significant yield risk - consider alternatives"
            ])
        
        return implications
    
    def _generate_risk_recommendations(self, risk_score: float) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if risk_score <= 0.3:
            recommendations.extend([
                "Excellent conditions for expansion loans",
                "Consider productivity enhancement investments"
            ])
        elif risk_score <= 0.5:
            recommendations.extend([
                "Standard financial planning approach",
                "Monitor conditions for optimal timing"
            ])
        elif risk_score <= 0.7:
            recommendations.extend([
                "Diversify crop portfolio",
                "Invest in drought-resistant varieties",
                "Consider micro-irrigation loans"
            ])
        else:
            recommendations.extend([
                "Delay major financial commitments",
                "Focus on risk mitigation measures",
                "Explore emergency funding options"
            ])
        
        return recommendations
    
    def _extract_loan_details(self, query_text: str) -> Dict[str, Any]:
        """Extract loan-specific details from query"""
        details = {}
        
        # Extract loan amount if mentioned
        amount_patterns = [
            r'(\d+)\s*(?:lakh|lacs|लाख)',
            r'(\d+)\s*(?:thousand|हजार)',
            r'(\d+)\s*(?:crore|करोड़)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, query_text.lower())
            if match:
                amount = int(match.group(1))
                if "lakh" in pattern or "लाख" in pattern:
                    details["requested_amount"] = amount * 100000
                elif "thousand" in pattern or "हजार" in pattern:
                    details["requested_amount"] = amount * 1000
                elif "crore" in pattern or "करोड़" in pattern:
                    details["requested_amount"] = amount * 10000000
                break
        
        # Extract loan purpose
        purpose_keywords = {
            "tractor": LoanType.FARM_MECHANIZATION,
            "ट्रैक्टर": LoanType.FARM_MECHANIZATION,
            "irrigation": LoanType.IRRIGATION,
            "सिंचाई": LoanType.IRRIGATION,
            "crop": LoanType.CROP_LOAN,
            "फसल": LoanType.CROP_LOAN,
            "dairy": LoanType.DAIRY,
            "डेयरी": LoanType.DAIRY
        }
        
        for keyword, loan_type in purpose_keywords.items():
            if keyword in query_text.lower():
                details["loan_purpose"] = loan_type
                break
        
        return details
    
    def _extract_subsidy_details(self, query_text: str) -> Dict[str, Any]:
        """Extract subsidy-specific details from query"""
        details = {}
        
        # Extract subsidy type
        subsidy_keywords = {
            "drip": SubsidyType.IRRIGATION_EQUIPMENT,
            "ड्रिप": SubsidyType.IRRIGATION_EQUIPMENT,
            "solar": SubsidyType.SOLAR_PUMP,
            "सोलर": SubsidyType.SOLAR_PUMP,
            "tractor": SubsidyType.FARM_MACHINERY,
            "ट्रैक्टर": SubsidyType.FARM_MACHINERY,
            "organic": SubsidyType.ORGANIC_FARMING,
            "जैविक": SubsidyType.ORGANIC_FARMING
        }
        
        for keyword, subsidy_type in subsidy_keywords.items():
            if keyword in query_text.lower():
                details["subsidy_type"] = subsidy_type
                break
        
        return details
    
    def _extract_policy_details(self, query_text: str) -> Dict[str, Any]:
        """Extract policy-specific information"""
        details = {}
        
        # Extract crop type for MSP queries
        crop_keywords = {
            "wheat": "wheat", "गेहूं": "wheat",
            "rice": "rice", "धान": "rice",
            "cotton": "cotton", "कपास": "cotton"
        }
        
        for keyword, crop in crop_keywords.items():
            if keyword in query_text.lower():
                details["crop_type"] = crop
                break
        
        return details
    
    def _extract_documentation_needs(self, query_text: str) -> Dict[str, Any]:
        """Extract documentation requirements"""
        details = {}
        
        doc_keywords = {
            "aadhaar": "aadhaar_card",
            "आधार": "aadhaar_card",
            "pan": "pan_card",
            "land": "land_documents",
            "जमीन": "land_documents"
        }
        
        required_docs = []
        for keyword, doc_type in doc_keywords.items():
            if keyword in query_text.lower():
                required_docs.append(doc_type)
        
        details["document_types"] = required_docs
        return details
    
    def _get_matching_keywords(self, query_lower: str) -> List[str]:
        """Get list of matching finance keywords"""
        all_keywords = [
            "loan", "subsidy", "scheme", "मsp", "insurance",
            "लोन", "सब्सिडी", "योजना", "बीमा"
        ]
        return [kw for kw in all_keywords if kw in query_lower]
    
    async def _assess_loan_eligibility(self, query: AgricultureQuery, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess loan eligibility for the farmer with satellite-enhanced risk analysis"""
        extracted_info = analysis.get("extracted_info", {})
        requested_amount = extracted_info.get("requested_amount", 100000)
        loan_purpose = extracted_info.get("loan_purpose", LoanType.CROP_LOAN)
        satellite_insights = analysis.get("satellite_insights", {})
        
        # Get relevant loan schemes
        relevant_schemes = self._get_relevant_loan_schemes(loan_purpose, requested_amount)
        
        assessments = []
        for scheme_id, scheme in relevant_schemes.items():
            assessment = self._evaluate_loan_eligibility(scheme, query.farm_profile, requested_amount)
            
            # Enhance assessment with satellite insights
            if satellite_insights:
                assessment = self._enhance_assessment_with_satellite_data(assessment, satellite_insights)
            
            assessments.append(assessment)
        
        # Sort by eligibility score
        assessments.sort(key=lambda x: x.eligibility_percentage, reverse=True)
        
        return {
            "response_type": "loan_assessment",
            "assessments": assessments[:3],  # Top 3 schemes
            "satellite_risk_analysis": satellite_insights,
            "general_recommendations": self._get_loan_recommendations(assessments, satellite_insights),
            "next_steps": self._get_loan_next_steps(assessments[0] if assessments else None)
        }
    
    def _get_relevant_loan_schemes(self, loan_purpose: LoanType, amount: float) -> Dict[str, LoanScheme]:
        """Get loan schemes relevant to farmer's needs"""
        relevant = {}
        
        for scheme_id, scheme in self.loan_schemes.items():
            # Check if scheme matches purpose and amount criteria
            if (scheme.loan_type == loan_purpose or loan_purpose == LoanType.CROP_LOAN) and \
               scheme.max_amount >= amount:
                relevant[scheme_id] = scheme
        
        # Always include KCC as it's universal
        if "kisan_credit_card" not in relevant:
            relevant["kisan_credit_card"] = self.loan_schemes["kisan_credit_card"]
        
        return relevant
    
    def _evaluate_loan_eligibility(self, scheme: LoanScheme, farm_profile: Optional[FarmProfile], amount: float) -> EligibilityAssessment:
        """Evaluate farmer's eligibility for a specific loan scheme"""
        eligibility_score = 100.0
        missing_criteria = []
        recommendations = []
        
        # Basic eligibility checks
        if amount > scheme.max_amount:
            eligibility_score -= 50
            missing_criteria.append(f"Requested amount exceeds maximum limit of ₹{scheme.max_amount:,.0f}")
        
        # Farm profile based assessment
        if farm_profile:
            # Farm size assessment
            if farm_profile.total_area < 1:  # Less than 1 acre (marginal farmer)
                if "Small farmers" not in scheme.target_beneficiaries:
                    eligibility_score -= 10
                else:
                    recommendations.append("You qualify for small farmer benefits")
            
            # Income assessment (if available)
            if hasattr(farm_profile, 'annual_income') and farm_profile.annual_income:
                if farm_profile.annual_income < 200000:  # Less than 2 lakh
                    recommendations.append("Consider interest subvention schemes")
        else:
            eligibility_score -= 20
            missing_criteria.append("Farm profile information needed for accurate assessment")
        
        # Document readiness (assumed based on common requirements)
        document_score = 85  # Assuming most farmers have basic documents
        eligibility_score = (eligibility_score + document_score) / 2
        
        eligible = eligibility_score > 60
        
        return EligibilityAssessment(
            scheme_name=scheme.scheme_name,
            eligible=eligible,
            confidence_score=min(eligibility_score / 100, 0.95),
            eligibility_percentage=eligibility_score,
            missing_criteria=missing_criteria,
            recommendations=recommendations,
            estimated_amount=min(amount, scheme.max_amount) if eligible else None,
            next_steps=self._get_scheme_next_steps(scheme, eligible)
        )
    
    def _get_scheme_next_steps(self, scheme: LoanScheme, eligible: bool) -> List[str]:
        """Get next steps for loan application"""
        if not eligible:
            return [
                "Improve eligibility criteria",
                "Consider alternative schemes",
                "Consult with bank relationship manager"
            ]
        
        return [
            f"Visit nearest {scheme.implementing_agency} branch",
            "Prepare required documents",
            f"Submit application within {scheme.processing_time_days} days processing time",
            "Follow up on application status"
        ]
    
    def _enhance_assessment_with_satellite_data(self, assessment: EligibilityAssessment, satellite_insights: Dict[str, Any]) -> EligibilityAssessment:
        """Enhance loan assessment with satellite risk analysis"""
        if not satellite_insights:
            return assessment
        
        risk_level = satellite_insights.get("risk_level", "unknown")
        risk_score = satellite_insights.get("overall_risk_score", 0.5)
        
        # Adjust eligibility based on satellite risk
        original_percentage = assessment.eligibility_percentage
        risk_adjustment = self._calculate_risk_adjustment(risk_score)
        
        # Apply risk adjustment (satellite data influences final assessment)
        adjusted_percentage = max(0, min(100, original_percentage + risk_adjustment))
        
        # Update assessment with satellite insights
        enhanced_recommendations = list(assessment.recommendations)
        enhanced_recommendations.extend(satellite_insights.get("recommendations", []))
        
        # Add satellite-specific recommendations
        if risk_level == "high" or risk_level == "very_high":
            enhanced_recommendations.extend([
                "Consider crop insurance given current environmental conditions",
                "Monitor weather patterns closely for optimal loan utilization"
            ])
        elif risk_level == "low":
            enhanced_recommendations.append("Favorable conditions for agricultural investments")
        
        return EligibilityAssessment(
            scheme_name=assessment.scheme_name,
            eligible=assessment.eligible,
            confidence_score=min(assessment.confidence_score + 0.1, 1.0),  # Satellite data increases confidence
            eligibility_percentage=adjusted_percentage,
            missing_criteria=assessment.missing_criteria,
            recommendations=enhanced_recommendations,
            estimated_amount=assessment.estimated_amount,
            next_steps=assessment.next_steps
        )
    
    def _calculate_risk_adjustment(self, risk_score: float) -> float:
        """Calculate eligibility adjustment based on satellite risk score"""
        if risk_score <= 0.3:
            return 5  # Low risk - slight boost
        elif risk_score <= 0.5:
            return 0  # Moderate risk - no change
        elif risk_score <= 0.7:
            return -3  # High risk - small penalty
        else:
            return -7  # Very high risk - larger penalty
    
    def _get_loan_recommendations(self, assessments: List[EligibilityAssessment], satellite_insights: Dict[str, Any] = None) -> List[str]:
        """Get general loan recommendations enhanced with satellite insights"""
        if not assessments:
            return ["Consult with agricultural extension officer for guidance"]
        
        recommendations = []
        best_assessment = assessments[0]
        
        if best_assessment.eligible:
            recommendations.append(f"You are eligible for {best_assessment.scheme_name}")
            if best_assessment.estimated_amount:
                recommendations.append(f"Estimated loan amount: ₹{best_assessment.estimated_amount:,.0f}")
        else:
            recommendations.append("Consider improving eligibility criteria")
            recommendations.append("Start with smaller loan amounts")
        
        # Add satellite-based financial recommendations
        if satellite_insights:
            risk_level = satellite_insights.get("risk_level", "unknown")
            financial_implications = satellite_insights.get("financial_implications", [])
            
            if risk_level == "low":
                recommendations.append("🛰️ Satellite data shows favorable conditions for agricultural investments")
                recommendations.append("Consider expanding loan amount for productivity improvements")
            elif risk_level == "moderate":
                recommendations.append("🛰️ Current environmental conditions are stable for planned investments")
            elif risk_level in ["high", "very_high"]:
                recommendations.append("🛰️ Satellite data indicates elevated risk - consider comprehensive insurance")
                recommendations.append("Plan loan utilization carefully given current environmental conditions")
            
            # Add specific financial implications
            recommendations.extend([f"💰 {impl}" for impl in financial_implications[:2]])
        
        recommendations.append("Maintain good credit history for future applications")
        return recommendations
    
    def _get_loan_next_steps(self, best_assessment: Optional[EligibilityAssessment]) -> List[str]:
        """Get immediate next steps for loan process"""
        if not best_assessment:
            return ["Consult with bank for personalized guidance"]
        
        return best_assessment.next_steps
    
    async def _recommend_subsidies(self, query: AgricultureQuery, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend appropriate subsidies for the farmer"""
        extracted_info = analysis.get("extracted_info", {})
        subsidy_type = extracted_info.get("subsidy_type")
        
        # Get relevant subsidies
        relevant_subsidies = self._get_relevant_subsidies(subsidy_type, query.farm_profile, query.location)
        
        return {
            "response_type": "subsidy_recommendations",
            "relevant_subsidies": relevant_subsidies,
            "application_guidance": self._get_subsidy_application_guidance(),
            "tips": self._get_subsidy_tips()
        }
    
    def _get_relevant_subsidies(self, subsidy_type: Optional[SubsidyType], 
                               farm_profile: Optional[FarmProfile], 
                               location: Optional[Location]) -> List[Dict[str, Any]]:
        """Get relevant subsidies based on farmer profile"""
        relevant = []
        
        for scheme_id, scheme in self.subsidy_schemes.items():
            if subsidy_type and scheme.subsidy_type != subsidy_type:
                continue
            
            # Calculate actual subsidy percentage based on farmer category
            actual_percentage = self._calculate_actual_subsidy_percentage(
                scheme, farm_profile, location
            )
            
            relevant.append({
                "scheme": scheme,
                "actual_subsidy_percentage": actual_percentage,
                "estimated_benefit": self._estimate_subsidy_benefit(scheme, actual_percentage),
                "urgency": self._assess_scheme_urgency(scheme)
            })
        
        # Sort by benefit amount
        relevant.sort(key=lambda x: x["estimated_benefit"], reverse=True)
        return relevant[:5]  # Top 5 relevant subsidies
    
    def _calculate_actual_subsidy_percentage(self, scheme: SubsidyScheme, 
                                           farm_profile: Optional[FarmProfile],
                                           location: Optional[Location]) -> float:
        """Calculate actual subsidy percentage based on farmer category"""
        base_percentage = scheme.subsidy_percentage
        
        # Apply category-specific benefits
        if farm_profile and farm_profile.total_area < 2:  # Small/marginal farmer
            if "SC/ST" in scheme.special_conditions[0] if scheme.special_conditions else "":
                return min(base_percentage + 20, 90)  # Additional benefits for SC/ST
            return min(base_percentage + 10, 80)  # Small farmer benefits
        
        return base_percentage
    
    def _estimate_subsidy_benefit(self, scheme: SubsidyScheme, actual_percentage: float) -> float:
        """Estimate potential subsidy benefit amount"""
        # Use max subsidy amount as baseline
        return scheme.max_subsidy_amount * (actual_percentage / 100)
    
    def _assess_scheme_urgency(self, scheme: SubsidyScheme) -> str:
        """Assess urgency of scheme application"""
        if "Annual budget allocation" in scheme.validity_period:
            return "High - Limited annual budget"
        elif "Ongoing" in scheme.validity_period:
            return "Medium - Apply when ready"
        else:
            return "Low - Check validity period"
    
    def _get_subsidy_application_guidance(self) -> List[str]:
        """Get general subsidy application guidance"""
        return [
            "Apply through official government portals",
            "Ensure all documents are properly attested",
            "Follow up regularly on application status",
            "Keep photocopies of all submitted documents",
            "Verify scheme details from official sources"
        ]
    
    def _get_subsidy_tips(self) -> List[str]:
        """Get tips for maximizing subsidy benefits"""
        return [
            "Apply early in the financial year for better allocation",
            "Join farmer groups for group subsidies",
            "Keep all purchase receipts for claim processing",
            "Verify vendor empanelment before purchase",
            "Consider combining multiple schemes for maximum benefit"
        ]
    
    async def _provide_policy_info(self, query: AgricultureQuery, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide policy and MSP information"""
        extracted_info = analysis.get("extracted_info", {})
        crop_type = extracted_info.get("crop_type")
        
        policy_info = {}
        
        # MSP information
        if crop_type and crop_type in self.policy_knowledge["msp_crops"]["kharif_2024"]:
            policy_info["msp"] = {
                "crop": crop_type,
                "current_price": self.policy_knowledge["msp_crops"]["kharif_2024"][crop_type],
                "season": "Kharif 2024",
                "procurement_info": "Available at designated centers"
            }
        
        # Insurance information
        policy_info["insurance"] = self.policy_knowledge["insurance_schemes"]["pmfby"]
        
        return {
            "response_type": "policy_information",
            "policy_details": policy_info,
            "recommendations": self._get_policy_recommendations(crop_type)
        }
    
    def _get_policy_recommendations(self, crop_type: Optional[str]) -> List[str]:
        """Get policy-related recommendations"""
        recommendations = [
            "Register for PMFBY crop insurance for risk protection",
            "Keep updated with MSP announcements",
            "Utilize e-NAM platform for better price discovery"
        ]
        
        if crop_type:
            recommendations.insert(0, f"Current MSP provides good returns for {crop_type}")
        
        return recommendations
    
    async def _assist_documentation(self, query: AgricultureQuery, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assist with documentation requirements"""
        extracted_info = analysis.get("extracted_info", {})
        doc_types = extracted_info.get("document_types", [])
        
        documentation_guide = {}
        
        # Common documents guide
        documentation_guide["common_documents"] = {
            "aadhaar_card": {
                "purpose": "Identity and address proof",
                "how_to_get": "Visit Aadhaar center or download from UIDAI portal",
                "validity": "Permanent",
                "required_for": "All government schemes"
            },
            "land_documents": {
                "purpose": "Land ownership proof",
                "documents": ["Khatiyan", "Khesra", "Mutation certificate", "Jamabandi"],
                "how_to_get": "Revenue department or Tehsil office",
                "validity": "As per revenue records"
            },
            "income_certificate": {
                "purpose": "Income proof for subsidies",
                "how_to_get": "Tehsil or Block office",
                "validity": "1 year",
                "required_for": "Most subsidy schemes"
            }
        }
        
        return {
            "response_type": "documentation_assistance",
            "documentation_guide": documentation_guide,
            "quick_tips": self._get_documentation_tips()
        }
    
    def _get_documentation_tips(self) -> List[str]:
        """Get documentation tips"""
        return [
            "Keep multiple photocopies of all documents",
            "Get documents attested by authorized officials",
            "Ensure all documents have consistent name spelling",
            "Keep digital copies for online applications",
            "Update documents before expiry dates"
        ]
    
    async def _general_finance_guidance(self, query: AgricultureQuery) -> Dict[str, Any]:
        """Provide general finance guidance"""
        return {
            "response_type": "general_guidance",
            "available_services": [
                "Loan eligibility assessment",
                "Subsidy scheme recommendations", 
                "Policy information",
                "Documentation assistance"
            ],
            "contact_information": {
                "toll_free": "1800-180-1551 (Kisan Call Center)",
                "portal": "pmkisan.gov.in",
                "local": "Contact nearest agriculture extension office"
            }
        }
    
    def _create_agent_response(self, response_data: Dict[str, Any], query: AgricultureQuery) -> AgentResponse:
        """Create structured agent response with satellite enhancement"""
        response_type = response_data.get("response_type", "general_guidance")
        satellite_insights = response_data.get("satellite_risk_analysis", {})
        
        # Determine confidence score based on satellite data availability
        base_confidence = 0.85
        satellite_confidence_boost = 0.1 if satellite_insights else 0.0
        final_confidence = min(0.99, base_confidence + satellite_confidence_boost)
        
        # Generate summary based on response type
        if response_type == "loan_assessment":
            summary = self._create_loan_summary(response_data)
            recommendations = self._create_loan_recommendations(response_data)
        elif response_type == "subsidy_recommendations":
            summary = self._create_subsidy_summary(response_data)
            recommendations = self._create_subsidy_recommendations(response_data)
        elif response_type == "policy_information":
            summary = self._create_policy_summary(response_data)
            recommendations = self._create_policy_recommendations(response_data)
        else:
            summary = "Agricultural finance and policy guidance available"
            recommendations = [{"title": "General Guidance", "description": "Contact Kisan Call Center for specific assistance"}]
        
        # Enhance summary with satellite insights
        if satellite_insights:
            risk_level = satellite_insights.get("risk_level", "unknown")
            summary += f"\n\n🛰️ Satellite Analysis: Current environmental conditions show {risk_level} risk level for agricultural activities."
        
        # Enhanced sources list
        sources = ["Government schemes database", "MSP announcements", "PMFBY guidelines"]
        if satellite_insights:
            sources.append("Satellite environmental monitoring")
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name="Finance & Policy Advisor (Satellite Enhanced)",
            query_id=query.query_id,
            response_text=summary,
            response_language=query.query_language,
            confidence_score=final_confidence,
            reasoning="Analyzed farmer profile and matched with appropriate schemes using satellite environmental data",
            recommendations=recommendations,
            sources=sources,
            next_steps=response_data.get("next_steps", []),
            timestamp=datetime.now(),
            processing_time_ms=250,
            metadata={
                "response_type": response_type,
                "schemes_analyzed": len(response_data.get("assessments", [])),
                "capabilities": self.finance_capabilities,
                "satellite_enhanced": bool(satellite_insights),
                "environmental_risk_level": satellite_insights.get("risk_level", "unknown") if satellite_insights else None
            }
        )
    
    def _create_loan_summary(self, response_data: Dict[str, Any]) -> str:
        """Create loan assessment summary"""
        assessments = response_data.get("assessments", [])
        if not assessments:
            return "कृषि ऋण की जानकारी के लिए स्थानीय बैंक से संपर्क करें।"
        
        best = assessments[0]
        if best.eligible:
            return f"आप {best.scheme_name} के लिए योग्य हैं। अनुमानित राशि: ₹{best.estimated_amount:,.0f}। {best.eligibility_percentage:.0f}% योग्यता स्कोर के साथ यह योजना आपके लिए उपयुक्त है।"
        else:
            return f"{best.scheme_name} के लिए कुछ शर्तें पूरी करनी होंगी। वर्तमान योग्यता: {best.eligibility_percentage:.0f}%।"
    
    def _create_loan_recommendations(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create loan recommendations"""
        recommendations = []
        assessments = response_data.get("assessments", [])
        
        for i, assessment in enumerate(assessments[:3]):
            priority = ["high", "medium", "low"][i]
            recommendations.append({
                "title": assessment.scheme_name,
                "description": f"योग्यता: {assessment.eligibility_percentage:.0f}% | ब्याज दर: {self.loan_schemes.get(assessment.scheme_name.lower().replace(' ', '_'), type('obj', (object,), {'interest_rate': 'N/A'})).interest_rate}%",
                "priority": priority,
                "action_required": "आवेदन करें" if assessment.eligible else "योग्यता बढ़ाएं"
            })
        
        return recommendations
    
    def _create_subsidy_summary(self, response_data: Dict[str, Any]) -> str:
        """Create subsidy summary"""
        subsidies = response_data.get("relevant_subsidies", [])
        if not subsidies:
            return "सब्सिडी योजनाओं की जानकारी के लिए कृषि विभाग से संपर्क करें।"
        
        best = subsidies[0]
        scheme = best["scheme"]
        return f"{scheme.scheme_name} में {best['actual_subsidy_percentage']:.0f}% सब्सिडी उपलब्ध। अनुमानित लाभ: ₹{best['estimated_benefit']:,.0f}। {best['urgency']} प्राथमिकता।"
    
    def _create_subsidy_recommendations(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create subsidy recommendations"""
        recommendations = []
        subsidies = response_data.get("relevant_subsidies", [])
        
        for subsidy in subsidies[:3]:
            scheme = subsidy["scheme"]
            recommendations.append({
                "title": scheme.scheme_name,
                "description": f"सब्सिडी: {subsidy['actual_subsidy_percentage']:.0f}% | अधिकतम राशि: ₹{scheme.max_subsidy_amount:,.0f}",
                "priority": "high" if subsidy["urgency"].startswith("High") else "medium",
                "action_required": "तुरंत आवेदन करें" if "High" in subsidy["urgency"] else "आवेदन करें"
            })
        
        return recommendations
    
    def _create_policy_summary(self, response_data: Dict[str, Any]) -> str:
        """Create policy information summary"""
        policy_details = response_data.get("policy_details", {})
        
        if "msp" in policy_details:
            msp = policy_details["msp"]
            return f"{msp['crop']} का वर्तमान MSP: ₹{msp['current_price']} प्रति क्विंटल। {msp['season']} सीजन के लिए। निर्धारित केंद्रों पर खरीद उपलब्ध।"
        
        return "नीतिगत जानकारी और MSP दरों के लिए संपर्क करें।"
    
    def _create_policy_recommendations(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create policy recommendations"""
        recommendations = response_data.get("recommendations", [])
        return [{"title": rec, "description": rec, "priority": "medium"} for rec in recommendations]
    
    def _create_error_response(self, query: AgricultureQuery, error: str) -> AgentResponse:
        """Create error response"""
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name="Finance & Policy Advisor",
            query_id=query.query_id,
            response_text="क्षमा करें, तकनीकी समस्या के कारण जानकारी प्रदान नहीं कर सकते। कृषि विभाग से संपर्क करें।",
            response_language=query.query_language,
            confidence_score=0.1,
            warnings=[f"Technical error: {error}"],
            timestamp=datetime.now(),
            metadata={"error": True, "error_message": error}
        )


# Test function for the Finance Policy Agent
async def test_finance_agent():
    """Test the Finance and Policy Agent"""
    agent = FinancePolicyAgent()
    
    print("🏦 Testing Finance and Policy Agent")
    
    # Test loan query
    loan_query = AgricultureQuery(
        query_text="मुझे ट्रैक्टर खरीदने के लिए 5 लाख का लोन चाहिए। मैं किसान क्रेडिट कार्ड के लिए योग्य हूं?",
        query_language=Language.MIXED,
        user_id="test_farmer",
        location=Location(state="Punjab", district="Ludhiana"),
        farm_profile=FarmProfile(
            farm_id="test_001",
            farmer_name="Test Farmer",
            location=Location(state="Punjab", district="Ludhiana"),
            total_area=5.0,
            soil_type=SoilType.ALLUVIAL,
            current_crops=[CropType.WHEAT],
            irrigation_type="tube_well",
            farm_type="small"
        )
    )
    
    print("🔄 Processing loan query...")
    response = await agent.process_query(loan_query)
    print(f"✅ Loan Response: {response.response_text[:200]}...")
    
    # Test subsidy query
    subsidy_query = AgricultureQuery(
        query_text="What subsidies are available for drip irrigation in Maharashtra?",
        query_language=Language.ENGLISH,
        user_id="test_farmer_2",
        location=Location(state="Maharashtra", district="Pune")
    )
    
    print("🔄 Processing subsidy query...")
    response2 = await agent.process_query(subsidy_query)
    print(f"✅ Subsidy Response: {response2.response_text[:200]}...")
    
    print("🎉 Finance and Policy Agent working successfully!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_finance_agent())
