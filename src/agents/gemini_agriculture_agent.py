"""
Gemini AI-powered agriculture agent using the latest Google GenAI SDK.
Integrates with the Multi-Agent Agriculture Advisory System.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

# Latest Google GenAI imports
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import our agriculture models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.core.agriculture_models import (
        AgricultureQuery, AgentResponse, QueryDomain, Language, 
        AgricultureCapability, CropType, SoilType, SeasonType
    )
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from core.agriculture_models import (
        AgricultureQuery, AgentResponse, QueryDomain, Language, 
        AgricultureCapability, CropType, SoilType, SeasonType
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class GeminiAgricultureAgent:
    """
    Advanced agriculture agent powered by Google's Gemini 2.5 models.
    Leverages the latest GenAI SDK for enhanced agricultural intelligence.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini agriculture agent"""
        
        # Load API key from environment or parameter
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable, "
                "or pass it as a parameter. Get your API key from: https://aistudio.google.com/apikey"
            )
        
        # Initialize Gemini client with latest SDK
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("✓ Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
        
        # Agent configuration
        self.agent_id = "gemini_agriculture_agent"
        self.agent_name = "Gemini Agriculture Expert"
        self.model_name = "gemini-2.5-flash"  # Latest recommended model
        self.capabilities = [
            AgricultureCapability.CROP_RECOMMENDATION,
            AgricultureCapability.PEST_IDENTIFICATION,
            AgricultureCapability.IRRIGATION_PLANNING,
            AgricultureCapability.YIELD_PREDICTION,
            AgricultureCapability.WEATHER_ANALYSIS,
            AgricultureCapability.MULTILINGUAL_NLP
        ]
        
        # Setup system instructions for agriculture domain
        self.system_instruction = self._create_agriculture_system_prompt()
        
        logger.info(f"✓ Gemini Agriculture Agent initialized with model: {self.model_name}")
    
    def _create_agriculture_system_prompt(self) -> str:
        """Create simple, effective system instructions for multilingual agriculture support"""
        
        return """You are an expert agricultural advisor for Indian farmers.

CAPABILITIES:
- Expert knowledge of Indian agriculture, crops, pests, irrigation, and farming practices
- Understand multiple languages: Hindi, English, and mixed Hindi-English (Hinglish)
- Respond in the same language the farmer uses
- Provide practical, cost-effective solutions

GUIDELINES:
- Give simple, actionable advice that farmers can implement
- Consider Indian climate, soil, and agricultural conditions
- Suggest both traditional and modern farming techniques
- Keep responses helpful and farmer-friendly
- Focus on practical solutions over complex theory

LANGUAGE: Always respond in the same language as the farmer's question. If they ask in Hindi, respond in Hindi. If they ask in English, respond in English. If they mix languages, respond naturally."""

    async def process_query(self, query: AgricultureQuery) -> AgentResponse:
        """
        Process an agriculture query using Gemini AI
        
        Args:
            query: AgricultureQuery object containing the user's question
            
        Returns:
            AgentResponse with Gemini-generated agricultural advice
        """
        
        try:
            # Prepare the query for Gemini
            enhanced_prompt = self._enhance_query_with_context(query)
            
            # Configure generation parameters
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                max_output_tokens=2000,
                temperature=0.7,  # Balanced creativity and accuracy
                candidate_count=1,
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                ]
            )
            
            # Generate response using Gemini
            start_time = datetime.now()
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=enhanced_prompt,
                config=config
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Parse and structure the response
            agricultural_response = self._parse_gemini_response(
                response, query, processing_time
            )
            
            logger.info(
                f"✓ Gemini query processed in {processing_time:.2f}s "
                f"with confidence: {agricultural_response.confidence:.2f}"
            )
            
            return agricultural_response
            
        except Exception as e:
            logger.error(f"Error processing query with Gemini: {e}")
            
            # Return error response
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                query_id=query.query_id,
                response_text=f"Error processing your agriculture query: {str(e)}",
                confidence_score=0.0,
                recommendations=[],
                metadata={
                    "error": str(e),
                    "model": self.model_name
                }
            )
    
    def _enhance_query_with_context(self, query: AgricultureQuery) -> str:
        """Create a simple, effective prompt that leverages Gemini's native multilingual capabilities"""
        
        # Simple agricultural context prompt that works in any language
        prompt = f"""You are an expert agricultural advisor helping Indian farmers. Please provide practical, actionable advice.

Farmer's Question: {query.query_text}

Please respond in the same language as the question. If the farmer asks in Hindi, respond in Hindi. If they ask in English, respond in English. If they mix languages (Hinglish), you can respond accordingly.

Focus on:
- Practical, implementable solutions
- Indian agricultural context
- Cost-effective methods
- Seasonal considerations (current month: {datetime.now().strftime('%B')})"""

        # Add farm context if available
        if query.farm_profile:
            context_details = []
            if query.farm_profile.farm_size:
                context_details.append(f"Farm size: {query.farm_profile.farm_size} hectares")
            if query.farm_profile.soil_type:
                context_details.append(f"Soil type: {query.farm_profile.soil_type}")
            if query.farm_profile.location:
                context_details.append(f"Location: {query.farm_profile.location}")
            
            if context_details:
                prompt += f"\n\nFarm Context: {', '.join(context_details)}"
        
        # Add location if available
        if query.location:
            prompt += f"\nLocation: {query.location}"
            
        return prompt
        
        if hasattr(query, 'query_domain') and query.query_domain in domain_instructions:
            enhanced_parts.append(f"FOCUS AREA: {domain_instructions[query.query_domain]}")
        
        # Combine all parts
        return "\n\n".join(enhanced_parts)
    
    def _parse_gemini_response(self, gemini_response, query: AgricultureQuery, processing_time: float) -> AgentResponse:
        """Parse Gemini response and convert to AgentResponse format"""
        
        try:
            response_text = gemini_response.text
            
            # Extract recommendations from the response
            recommendations = self._extract_recommendations(response_text)
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(gemini_response, response_text)
            
            # Extract metadata
            metadata = {
                "model": self.model_name,
                "processing_time": processing_time,
                "response_length": len(response_text),
                "recommendations_count": len(recommendations),
                "gemini_candidate_count": len(gemini_response.candidates) if hasattr(gemini_response, 'candidates') else 1
            }
            
            # Add safety ratings if available
            if hasattr(gemini_response, 'candidates') and gemini_response.candidates:
                candidate = gemini_response.candidates[0]
                if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                    metadata["safety_ratings"] = {
                        rating.category: rating.probability for rating in candidate.safety_ratings
                    }
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                query_id=query.query_id,
                response_text=response_text,
                confidence_score=confidence,
                recommendations=recommendations,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                query_id=query.query_id,
                response_text="Error parsing the AI response",
                confidence_score=0.0,
                recommendations=[],
                metadata={"error": str(e)}
            )
    
    def _extract_recommendations(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract actionable recommendations from Gemini response"""
        
        recommendations = []
        
        # Common recommendation indicators
        recommendation_markers = [
            "recommended", "suggest", "advice", "should", "consider",
            "सुझाव", "सिफारिश", "करना चाहिए", "उपयोग करें"
        ]
        
        # Split response into sentences
        sentences = response_text.replace('\n', ' ').split('.')
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) > 20:  # Filter out very short sentences
                # Check if sentence contains recommendation indicators
                if any(marker.lower() in sentence.lower() for marker in recommendation_markers):
                    recommendations.append({
                        "id": f"rec_{i+1}",
                        "text": sentence,
                        "type": "suggestion",
                        "priority": "medium"
                    })
                
                # Check for numbered/bulleted recommendations
                if sentence.startswith(('1.', '2.', '3.', '•', '-', '*')):
                    clean_rec = sentence.lstrip('123456789.-•* ')
                    if len(clean_rec) > 15:
                        recommendations.append({
                            "id": f"rec_{i+1}",
                            "text": clean_rec,
                            "type": "action_item",
                            "priority": "high"
                        })
        
        # Limit to top 10 recommendations to avoid overwhelming
        return recommendations[:10]
    
    def _calculate_confidence(self, gemini_response, response_text: str) -> float:
        """Calculate confidence score based on response quality indicators"""
        
        confidence = 0.5  # Base confidence
        
        # Response length indicates detail (longer = higher confidence)
        if len(response_text) > 200:
            confidence += 0.2
        if len(response_text) > 500:
            confidence += 0.1
        
        # Check for specific agricultural terms (indicates domain relevance)
        agricultural_terms = [
            'crop', 'soil', 'fertilizer', 'irrigation', 'pest', 'disease',
            'variety', 'yield', 'harvest', 'sowing', 'farming',
            'फसल', 'मिट्टी', 'खाद', 'सिंचाई', 'कीट', 'रोग'
        ]
        
        term_count = sum(1 for term in agricultural_terms if term.lower() in response_text.lower())
        confidence += min(term_count * 0.02, 0.2)  # Max 0.2 boost from terms
        
        # Check for specific recommendations (actionable advice)
        if "recommend" in response_text.lower() or "सुझाव" in response_text:
            confidence += 0.1
        
        # Check if response was blocked by safety filters
        if hasattr(gemini_response, 'candidates') and gemini_response.candidates:
            candidate = gemini_response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                if candidate.finish_reason == "SAFETY":
                    confidence -= 0.3
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, confidence))
    
    async def process_multimodal_query(self, query: AgricultureQuery, image_path: Optional[str] = None) -> AgentResponse:
        """
        Process a query with optional image input (for crop/pest identification)
        
        Args:
            query: AgricultureQuery object
            image_path: Optional path to image file
            
        Returns:
            AgentResponse with multimodal analysis
        """
        
        try:
            # Prepare content list
            contents = []
            
            # Add text query
            enhanced_prompt = self._enhance_query_with_context(query)
            contents.append(enhanced_prompt)
            
            # Add image if provided
            if image_path and os.path.exists(image_path):
                from PIL import Image
                image = Image.open(image_path)
                contents.append(image)
                contents.append("Please analyze this image in the context of the agricultural question above.")
            
            # Configure generation
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                max_output_tokens=2500,  # More tokens for image analysis
                temperature=0.6,
            )
            
            # Generate response
            start_time = datetime.now()
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Parse response
            agricultural_response = self._parse_gemini_response(
                response, query, processing_time
            )
            
            # Add multimodal metadata
            agricultural_response.metadata["multimodal"] = True
            if image_path:
                agricultural_response.metadata["image_analyzed"] = True
                agricultural_response.metadata["image_path"] = image_path
            
            logger.info(f"✓ Multimodal query processed in {processing_time:.2f}s")
            
            return agricultural_response
            
        except Exception as e:
            logger.error(f"Error in multimodal processing: {e}")
            return await self.process_query(query)  # Fallback to text-only
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        
        return {
            "agent_id": self.agent_id,
            "model": self.model_name,
            "capabilities": [cap.value for cap in self.capabilities],
            "supported_languages": ["English", "Hindi", "Mixed (Hinglish)"],
            "multimodal_support": True,
            "api_provider": "Google Gemini",
            "sdk_version": "google-genai 1.29.0+",
            "specialization": "Indian Agriculture Advisory"
        }


async def test_gemini_agent():
    """Test function for the Gemini Agriculture Agent"""
    
    print("🌾 Testing Gemini Agriculture Agent...")
    
    try:
        # Initialize agent (will fail gracefully if no API key)
        agent = GeminiAgricultureAgent()
        
        # Test queries
        test_queries = [
            {
                "text": "What wheat variety is best for Punjab soil in Rabi season?",
                "lang": Language.ENGLISH,
                "description": "Crop recommendation query"
            },
            {
                "text": "मेरे गेहूं की फसल पर पीले धब्बे हैं, क्या करूं?",
                "lang": Language.HINDI,
                "description": "Pest management query in Hindi"
            },
            {
                "text": "Cotton की crop में कितना पानी लगता है per acre?",
                "lang": Language.MIXED,
                "description": "Irrigation query in Hinglish"
            }
        ]
        
        print(f"Agent Info: {agent.get_agent_info()}")
        print("\n" + "="*60)
        
        for i, test in enumerate(test_queries, 1):
            print(f"\nTest {i}: {test['description']}")
            print(f"Query: {test['text']}")
            
            # Create query object
            query = AgricultureQuery(
                query_text=test['text'],
                query_language=test['lang'],
                user_id=f"test_user_{i}"
            )
            
            # Process query
            response = await agent.process_query(query)
            
            # Display results
            print(f"Status: {response.status}")
            print(f"Confidence: {response.confidence:.2f}")
            print(f"Processing Time: {response.processing_time:.2f}s")
            print(f"Response Length: {len(response.response_text)} chars")
            print(f"Recommendations: {len(response.recommendations)}")
            
            if response.status == "completed":
                print("✓ Query processed successfully")
                # Show first 200 chars of response
                preview = response.response_text[:200] + "..." if len(response.response_text) > 200 else response.response_text
                print(f"Response Preview: {preview}")
            else:
                print(f"✗ Query failed: {response.response_text}")
            
            print("-" * 40)
        
        print("\n🎉 Gemini Agriculture Agent testing completed!")
        return True
        
    except ValueError as e:
        if "API key not found" in str(e):
            print("⚠️  Gemini API key not configured.")
            print("To use Gemini agent, set your API key:")
            print("1. Get API key from: https://aistudio.google.com/apikey")
            print("2. Set environment variable: GOOGLE_API_KEY=your_api_key")
            print("3. Or create .env file with: GOOGLE_API_KEY=your_api_key")
            return False
        else:
            print(f"✗ Error: {e}")
            return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_gemini_agent())
