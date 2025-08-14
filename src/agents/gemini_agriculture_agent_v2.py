"""
Production-Ready Gemini Agriculture Agent
Advanced AI-powered agricultural advisor using Google Gemini
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import re

# Set API key from environment or direct assignment
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyACHvqkA6UHMcZwSnhSuB50lhrnJzxOAjg')
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

# Gemini AI imports
import google.generativeai as genai

# Agriculture models
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agriculture_models import (
    AgricultureQuery, AgentResponse, QueryDomain, Language, 
    CropType, SeasonType, SoilType, Location, FarmProfile
)

logger = logging.getLogger(__name__)


class GeminiAgricultureAgent:
    """
    Advanced Gemini-powered agriculture agent
    Provides comprehensive agricultural advice using Google's Gemini AI
    """
    
    def __init__(self):
        self.agent_id = "gemini_agriculture_agent"
        self.agent_name = "Gemini Agriculture Expert"
        self.capabilities = [
            "crop_recommendation",
            "pest_identification", 
            "yield_prediction",
            "irrigation_planning",
            "finance_advisory",
            "market_analysis",
            "multilingual_support",
            "contextual_reasoning",
            "real_time_guidance"
        ]
        
        # Initialize Gemini
        self._setup_gemini()
        
        # Enhanced agricultural knowledge base
        self.agriculture_context = """
        आप एक विशेषज्ञ भारतीय कृषि सलाहकार हैं। आपको भारत की कृषि परिस्थितियों, फसलों, और किसानों की समस्याओं की गहरी जानकारी है।

        मुख्य संदर्भ:
        • भारत की 15 कृषि-जलवायु क्षेत्र
        • मुख्य मौसम: खरीफ (जून-अक्टूबर), रबी (नवंबर-अप्रैल), जायद (अप्रैल-जून)
        • प्रमुख फसलें: धान, गेहूं, कपास, गन्ना, दालें, तिलहन
        • मिट्टी के प्रकार: जलोढ़, काली (रेगुर), लाल, लेटेराइट, रेगिस्तानी, पर्वतीय
        
        क्षेत्रीय विशेषताएं:
        • पंजाब/हरियाणा: गेहूं-धान बेल्ट, उच्च मशीनीकरण
        • महाराष्ट्र: कपास, गन्ना, सोयाबीन
        • तमिलनाडु: धान, कपास, गन्ना
        • राजस्थान: बाजरा, दालें, तिलहन (शुष्क क्षेत्र)
        • पश्चिम बंगाल: धान, जूट, चाय
        • केरल: मसाले, नारियल, रबर
        
        सलाह में शामिल करें:
        ✓ स्थानीय जलवायु और मिट्टी की स्थिति
        ✓ पानी की उपलब्धता और सिंचाई के तरीके
        ✓ क्षेत्र के लिए उपयुक्त फसल किस्में
        ✓ कीट और रोग प्रबंधन
        ✓ बाजार की स्थिति और लाभप्रदता
        ✓ टिकाऊ खेती के तरीके
        ✓ लागत प्रभावी समाधान
        ✓ सरकारी योजनाएं और सब्सिडी
        """
    
    def _setup_gemini(self):
        """Initialize Gemini AI with API key"""
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Use Gemini 1.5 Flash for optimal performance and cost
            self.gemini_model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 0.7,  # Balanced creativity
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            logger.info("✅ Gemini AI initialized successfully")
            self.gemini_available = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.gemini_model = None
            self.gemini_available = False
    
    async def process_query(self, query: AgricultureQuery) -> AgentResponse:
        """Process agriculture query using Gemini AI"""
        
        if not self.gemini_available:
            return self._fallback_response(query)
        
        try:
            start_time = datetime.now()
            
            # Build comprehensive prompt
            prompt = self._build_enhanced_prompt(query)
            
            # Generate response using Gemini
            response = self.gemini_model.generate_content(prompt)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Parse and structure the response
            structured_response = self._create_agent_response(response.text, query, processing_time)
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Gemini processing failed: {e}")
            return self._error_response(query, str(e))
    
    def _build_enhanced_prompt(self, query: AgricultureQuery) -> str:
        """Build comprehensive agricultural prompt for Gemini"""
        
        prompt = f"{self.agriculture_context}\n\n"
        
        # Core query information
        prompt += f"किसान का प्रश्न: {query.query_text}\n"
        prompt += f"भाषा: {query.query_language.value}\n"
        
        # Add contextual information
        if query.location:
            prompt += f"स्थान: {query.location.state}"
            if query.location.district:
                prompt += f", {query.location.district}"
            prompt += "\n"
        
        if query.farm_profile:
            prompt += f"खेत की जानकारी:\n"
            prompt += f"• आकार: {query.farm_profile.total_area} एकड़ ({query.farm_profile.total_area * 0.4:.1f} हेक्टेयर)\n"
            prompt += f"• मिट्टी का प्रकार: {query.farm_profile.soil_type.value}\n"
            prompt += f"• सिंचाई: {query.farm_profile.irrigation_type}\n"
            prompt += f"• खेत का प्रकार: {query.farm_profile.farm_type}\n"
        
        # Current context
        current_month = datetime.now().strftime("%B")
        current_season = self._get_current_season()
        prompt += f"वर्तमान समय: {current_month} {datetime.now().year} ({current_season})\n\n"
        
        # Response instructions
        prompt += """
        निर्देश:
        1. व्यावहारिक और स्पष्ट सलाह दें
        2. स्थानीय परिस्थितियों को ध्यान में रखें
        3. लागत प्रभावी समाधान सुझाएं
        4. छोटे किसानों के लिए उपयुक्त हो
        5. यदि संभव हो तो सरकारी योजनाओं का उल्लेख करें
        6. चरणबद्ध कार्य योजना दें
        7. संभावित जोखिमों की चेतावनी दें
        
        उत्तर की भाषा: प्रश्न की भाषा के अनुसार (हिंदी/अंग्रेजी/मिश्रित)
        """
        
        return prompt
    
    def _get_current_season(self) -> str:
        """Determine current agricultural season"""
        month = datetime.now().month
        if 6 <= month <= 10:
            return "खरीफ मौसम"
        elif 11 <= month <= 4:
            return "रबी मौसम"
        else:
            return "जायद मौसम"
    
    def _create_agent_response(self, gemini_text: str, query: AgricultureQuery, processing_time: float) -> AgentResponse:
        """Create structured AgentResponse from Gemini output"""
        
        # Extract key recommendations from the text
        recommendations = self._extract_recommendations(gemini_text)
        
        # Extract warnings/cautions
        warnings = self._extract_warnings(gemini_text)
        
        # Extract next steps
        next_steps = self._extract_next_steps(gemini_text)
        
        # Determine confidence based on response quality
        confidence = self._calculate_confidence(gemini_text, query)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            query_id=query.query_id,
            response_text=gemini_text,
            response_language=query.query_language,
            confidence_score=confidence,
            reasoning="Gemini AI analyzed query using comprehensive agricultural knowledge base",
            recommendations=recommendations,
            warnings=warnings,
            next_steps=next_steps,
            timestamp=datetime.now(),
            processing_time_ms=int(processing_time),
            metadata={
                "model": "gemini-1.5-flash",
                "api_key_configured": True,
                "response_length": len(gemini_text),
                "capabilities_used": self.capabilities
            }
        )
    
    def _extract_recommendations(self, text: str) -> List[Dict[str, Any]]:
        """Extract actionable recommendations from Gemini response"""
        recommendations = []
        
        # Look for numbered points, bullet points, or suggestion patterns
        patterns = [
            r'(?:^|\n)(\d+\.?\s+[^\n]+)',  # Numbered lists
            r'(?:^|\n)([•*-]\s+[^\n]+)',   # Bullet points
            r'(?:सुझाव|सिफारिश|राय):\s*([^\n]+)',  # Hindi suggestions
            r'(?:recommend|suggest|advice):\s*([^\n]+)',  # English suggestions
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:  # Filter out short matches
                    recommendations.append({
                        "title": match.strip()[:50] + "..." if len(match) > 50 else match.strip(),
                        "description": match.strip(),
                        "priority": "medium",
                        "category": "general"
                    })
        
        # If no structured recommendations found, create from main content
        if not recommendations:
            lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 20]
            for i, line in enumerate(lines[:3]):  # Take first 3 substantial lines
                recommendations.append({
                    "title": f"सुझाव {i+1}",
                    "description": line,
                    "priority": "medium" if i == 0 else "low",
                    "category": "general"
                })
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _extract_warnings(self, text: str) -> List[str]:
        """Extract warnings/cautions from the response"""
        warnings = []
        
        warning_patterns = [
            r'(?:चेतावनी|सावधानी|खतरा|जोखिम|नुकसान):\s*([^\n]+)',
            r'(?:warning|caution|risk|danger|avoid):\s*([^\n]+)',
            r'(?:ध्यान|सावधान)\s+(?:रखें|रहें):\s*([^\n]+)'
        ]
        
        for pattern in warning_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            warnings.extend([match.strip() for match in matches])
        
        return warnings[:3]  # Limit to 3 warnings
    
    def _extract_next_steps(self, text: str) -> List[str]:
        """Extract next steps/action items"""
        next_steps = []
        
        step_patterns = [
            r'(?:अगला कदम|अगली कार्रवाई|करने योग्य):\s*([^\n]+)',
            r'(?:next step|action|follow up):\s*([^\n]+)',
            r'(?:^|\n)(?:तुरंत|अब|इस सप्ताह)\s+([^\n]+)'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            next_steps.extend([match.strip() for match in matches])
        
        return next_steps[:4]  # Limit to 4 next steps
    
    def _calculate_confidence(self, text: str, query: AgricultureQuery) -> float:
        """Calculate confidence score based on response quality"""
        confidence = 0.7  # Base confidence
        
        # Increase confidence for specific factors
        if len(text) > 200:  # Detailed response
            confidence += 0.1
        
        if any(word in text.lower() for word in ['किस्म', 'variety', 'फसल', 'crop']):
            confidence += 0.05
        
        if any(word in text.lower() for word in ['मिट्टी', 'soil', 'सिंचाई', 'irrigation']):
            confidence += 0.05
        
        if any(word in text.lower() for word in ['लागत', 'cost', 'price', 'मूल्य']):
            confidence += 0.05
        
        # Location-specific advice
        if query.location and query.location.state.lower() in text.lower():
            confidence += 0.05
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _fallback_response(self, query: AgricultureQuery) -> AgentResponse:
        """Provide fallback response when Gemini is unavailable"""
        
        fallback_advice = {
            "गेहूं": "HD-2967, DBW-88, या WH-147 जैसी किस्में आपके क्षेत्र के लिए उपयुक्त हो सकती हैं।",
            "धान": "MTU-1010, स्वर्णा, या BPT-5204 जैसी किस्में क्षेत्र के अनुसार चुनें।",
            "कपास": "Bt कपास की किस्में जैसे RCH-2, मल्लिका का चयन करें।",
            "wheat": "Consider varieties like HD-2967, DBW-88, or WH-147 for your region.",
            "rice": "Choose varieties like MTU-1010, Swarna, or BPT-5204 based on your area.",
        }
        
        query_lower = query.query_text.lower()
        advice = "सामान्य कृषि मार्गदर्शन उपलब्ध कराया गया है। विस्तृत सलाह के लिए स्थानीय कृषि विशेषज्ञ से संपर्क करें।"
        
        for crop, suggestion in fallback_advice.items():
            if crop in query_lower:
                advice = suggestion
                break
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            query_id=query.query_id,
            response_text=advice,
            response_language=query.query_language,
            confidence_score=0.5,
            reasoning="Fallback response - Gemini AI unavailable",
            recommendations=[{
                "title": "बुनियादी कृषि सलाह",
                "description": advice,
                "priority": "medium",
                "category": "fallback"
            }],
            timestamp=datetime.now(),
            metadata={"fallback": True, "reason": "Gemini unavailable"}
        )
    
    def _error_response(self, query: AgricultureQuery, error: str) -> AgentResponse:
        """Provide error response"""
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            query_id=query.query_id,
            response_text=f"क्षमा करें, तकनीकी समस्या के कारण विस्तृत सलाह नहीं दे सकते। कृपया बाद में प्रयास करें।",
            response_language=query.query_language,
            confidence_score=0.1,
            reasoning=f"Error occurred: {error}",
            warnings=[f"Technical error: {error}"],
            timestamp=datetime.now(),
            metadata={"error": True, "error_message": error}
        )
    
    def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return self.capabilities
    
    def is_available(self) -> bool:
        """Check if Gemini agent is available"""
        return self.gemini_available
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "model": "gemini-1.5-flash",
            "capabilities": self.capabilities,
            "available": self.gemini_available,
            "api_configured": bool(GOOGLE_API_KEY),
            "languages": ["hindi", "english", "mixed"],
            "specialization": "Indian Agriculture"
        }


# Test function
async def test_gemini_agent():
    """Test the Gemini agriculture agent"""
    
    agent = GeminiAgricultureAgent()
    
    print("🧪 Testing Enhanced Gemini Agriculture Agent")
    print(f"Agent Info: {agent.get_agent_info()}")
    
    if agent.is_available():
        print("✅ Gemini AI is available and configured")
        
        # Test with Hindi query
        test_query = AgricultureQuery(
            query_text="मेरे पास 3 हेक्टेयर जमीन है राजस्थान में। कम पानी में कौन सी फसल उगा सकते हैं?",
            query_language=Language.MIXED,
            user_id="test_farmer",
            location=Location(state="Rajasthan", district="Jodhpur"),
            farm_profile=FarmProfile(
                farm_id="test_farm_001",
                farmer_name="Test Farmer",
                location=Location(state="Rajasthan", district="Jodhpur"),
                total_area=7.5,  # 3 hectares = 7.5 acres approximately
                soil_type=SoilType.SANDY,
                current_crops=[CropType.MILLET],
                irrigation_type="rainfed",
                farm_type="small"
            )
        )
        
        print("\n🔄 Processing complex Hindi query...")
        response = await agent.process_query(test_query)
        
        print(f"✅ Response generated!")
        print(f"Agent: {response.agent_name}")
        print(f"Confidence: {response.confidence_score:.2f}")
        print(f"Processing Time: {response.processing_time_ms}ms")
        print(f"Response Length: {len(response.response_text)} characters")
        print(f"Recommendations: {len(response.recommendations)}")
        print(f"Warnings: {len(response.warnings)}")
        print(f"Next Steps: {len(response.next_steps)}")
        
        print(f"\nResponse Preview: {response.response_text[:200]}...")
        
        if response.recommendations:
            print("\nTop Recommendation:")
            print(f"  {response.recommendations[0]['title']}")
        
        return True
    else:
        print("⚠️  Gemini not available")
        return False


if __name__ == "__main__":
    asyncio.run(test_gemini_agent())
