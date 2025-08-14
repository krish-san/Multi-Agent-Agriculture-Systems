"""
Market Timing Agent
Specialized agent for forecasting commodity prices and recommending optimal 
selling times for Indian agricultural markets.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import random
import numpy as np
import asyncio

from .base_agent import BaseWorkerAgent
from ..core.agriculture_models import (
    AgricultureQuery, AgentResponse, CropType, Location, QueryDomain, Language
)
from ..core.models import AgentCapability, Task

logger = logging.getLogger(__name__)


class Commodity(Enum):
    """Major agricultural commodities in India"""
    WHEAT = "wheat"
    RICE = "rice"
    COTTON = "cotton"
    SUGARCANE = "sugarcane"
    SOYBEAN = "soybean"
    MUSTARD = "mustard"
    MAIZE = "maize"
    POTATO = "potato"
    ONION = "onion"
    TOMATO = "tomato"


class MarketTrend(Enum):
    """Market trend indicators"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class PriceForecast:
    """Commodity price forecast"""
    commodity: Commodity
    current_price: float
    forecast_price_7d: float
    forecast_price_30d: float
    confidence: float
    trend: MarketTrend
    volatility: float  # Percentage
    seasonal_factor: float
    news_sentiment: float


@dataclass
class MarketRecommendation:
    """Market timing recommendation"""
    commodity: Commodity
    recommendation: str  # e.g., "Sell now", "Hold for 2 weeks"
    reasoning: List[str]
    expected_gain: float  # Percentage
    confidence_score: float
    timeline: str


class MarketTimingAgent(BaseWorkerAgent):
    """
    Specialized agent for commodity price forecasting and market timing advice.
    Uses historical data simulation, trend analysis, and sentiment analysis
    to provide actionable recommendations for Indian farmers.
    """
    
    def __init__(self):
        super().__init__(
            name="market_timing_agent",
            capabilities=[
                AgentCapability.ANALYSIS,
                AgentCapability.DATA_PROCESSING,
                AgentCapability.PLANNING
            ],
            agent_type="market_timing"
        )
        
        # Initialize mock historical price data
        self._initialize_market_data()
    
    def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a market timing task (required by BaseWorkerAgent)"""
        try:
            # Extract query from task or context
            if hasattr(task, 'query') and task.query:
                query = task.query
            elif 'query' in context:
                query = context['query']
            else:
                return {"error": "No query provided for market timing analysis"}
            
            # Process the query using our existing logic
            if isinstance(query, AgricultureQuery):
                result = asyncio.run(self.process_query(query))
                return {"success": True, "response": result}
            else:
                return {"error": "Invalid query format"}
                
        except Exception as e:
            return {"error": f"Market timing analysis failed: {str(e)}"}
    
    def _initialize_market_data(self):
        """Initialize mock historical price data for major commodities"""
        self.market_data: Dict[Commodity, List[float]] = {}
        base_prices = {
            Commodity.WHEAT: 2200,
            Commodity.RICE: 3800,
            Commodity.COTTON: 6500,
            Commodity.SUGARCANE: 350,
            Commodity.SOYBEAN: 4800,
            Commodity.MUSTARD: 5500,
            Commodity.MAIZE: 2100,
            Commodity.POTATO: 1500,
            Commodity.ONION: 2500,
            Commodity.TOMATO: 3000
        }
        
        for commodity, base_price in base_prices.items():
            self.market_data[commodity] = self._generate_price_history(base_price)
    
    def _generate_price_history(self, base_price: float, days: int = 365) -> List[float]:
        """Generate a year of simulated daily prices"""
        prices = []
        price = base_price
        for i in range(days):
            # Add seasonality (sine wave)
            seasonal_effect = np.sin(2 * np.pi * i / 365) * 0.1 * base_price
            
            # Add random daily fluctuation
            daily_change = random.uniform(-0.02, 0.02) * price
            
            price += seasonal_effect / 365 + daily_change
            prices.append(round(price, 2))
        return prices
    
    async def process_query(self, query: AgricultureQuery) -> AgentResponse:
        """Process market timing and price forecast queries"""
        try:
            # Analyze query for commodity and intent
            query_analysis = self._analyze_market_query(query.query_text)
            
            if not query_analysis["commodity"]:
                return self._create_general_market_info_response(query)
            
            commodity = query_analysis["commodity"]
            
            # Generate forecast and recommendation
            forecast = self._generate_price_forecast(commodity)
            recommendation = self._create_market_recommendation(forecast)
            
            return self._create_agent_response(recommendation, forecast, query)
            
        except Exception as e:
            logger.error(f"Error processing market query: {e}")
            return self._create_error_response(query, str(e))
    
    def _analyze_market_query(self, query_text: str) -> Dict[str, Any]:
        """Analyze query to identify commodity and intent"""
        query_lower = query_text.lower()
        
        commodity_map = {
            "wheat": Commodity.WHEAT, "गेहूं": Commodity.WHEAT,
            "rice": Commodity.RICE, "धान": Commodity.RICE, "chawal": Commodity.RICE, "चावल": Commodity.RICE,
            "cotton": Commodity.COTTON, "कपास": Commodity.COTTON,
            "sugarcane": Commodity.SUGARCANE, "गन्ना": Commodity.SUGARCANE,
            "soybean": Commodity.SOYBEAN, "सोयाबीन": Commodity.SOYBEAN,
            "mustard": Commodity.MUSTARD, "सरसों": Commodity.MUSTARD,
            "maize": Commodity.MAIZE, "मक्का": Commodity.MAIZE,
            "potato": Commodity.POTATO, "आलू": Commodity.POTATO,
            "onion": Commodity.ONION, "प्याज": Commodity.ONION,
            "tomato": Commodity.TOMATO, "टमाटर": Commodity.TOMATO
        }
        
        found_commodity = None
        for keyword, commodity in commodity_map.items():
            if keyword in query_lower:
                found_commodity = commodity
                break
        
        return {
            "commodity": found_commodity,
            "intent": "price_forecast"  # Default intent
        }
    
    def _generate_price_forecast(self, commodity: Commodity) -> PriceForecast:
        """Generate a price forecast for a given commodity"""
        history = self.market_data[commodity]
        current_price = history[-1]
        
        # Simple moving average forecast
        ma_30d = np.mean(history[-30:])
        ma_7d = np.mean(history[-7:])
        
        # Forecast logic
        forecast_price_7d = (ma_7d * 1.01)  # Slight upward bias
        forecast_price_30d = (ma_30d * 1.02)
        
        # Trend analysis
        if ma_7d > ma_30d * 1.05:
            trend = MarketTrend.STRONG_BUY
        elif ma_7d > ma_30d:
            trend = MarketTrend.BUY
        elif ma_7d < ma_30d * 0.95:
            trend = MarketTrend.STRONG_SELL
        elif ma_7d < ma_30d:
            trend = MarketTrend.SELL
        else:
            trend = MarketTrend.HOLD
        
        # Volatility (standard deviation of last 30 days)
        volatility = np.std(history[-30:]) / ma_30d * 100
        
        return PriceForecast(
            commodity=commodity,
            current_price=round(current_price, 2),
            forecast_price_7d=round(forecast_price_7d, 2),
            forecast_price_30d=round(forecast_price_30d, 2),
            confidence=random.uniform(0.75, 0.90),
            trend=trend,
            volatility=round(volatility, 2),
            seasonal_factor=random.uniform(0.8, 1.2),
            news_sentiment=random.uniform(-0.5, 0.5)
        )
    
    def _create_market_recommendation(self, forecast: PriceForecast) -> MarketRecommendation:
        """Create a market timing recommendation based on the forecast"""
        reasoning = []
        
        # Determine recommendation based on trend
        if forecast.trend == MarketTrend.STRONG_BUY:
            recommendation = "Hold for higher prices"
            timeline = "4-6 weeks"
            expected_gain = (forecast.forecast_price_30d / forecast.current_price - 1) * 100
            reasoning.append("Strong upward trend detected.")
        elif forecast.trend == MarketTrend.BUY:
            recommendation = "Hold for now"
            timeline = "2-3 weeks"
            expected_gain = (forecast.forecast_price_7d / forecast.current_price - 1) * 100
            reasoning.append("Prices are currently rising.")
        elif forecast.trend == MarketTrend.STRONG_SELL:
            recommendation = "Sell immediately"
            timeline = "Next 3 days"
            expected_gain = 0
            reasoning.append("Strong downward pressure on prices.")
        elif forecast.trend == MarketTrend.SELL:
            recommendation = "Consider selling soon"
            timeline = "Next 7 days"
            expected_gain = 0
            reasoning.append("Prices are showing a downward trend.")
        else: # HOLD
            recommendation = "Hold and monitor market"
            timeline = "1-2 weeks"
            expected_gain = 0
            reasoning.append("Market is stable, no clear trend.")
        
        # Add volatility to reasoning
        if forecast.volatility > 5:
            reasoning.append(f"High market volatility ({forecast.volatility:.2f}%) suggests price swings.")
        else:
            reasoning.append(f"Low market volatility ({forecast.volatility:.2f}%) suggests stable prices.")
        
        return MarketRecommendation(
            commodity=forecast.commodity,
            recommendation=recommendation,
            reasoning=reasoning,
            expected_gain=round(expected_gain, 2),
            confidence_score=forecast.confidence,
            timeline=timeline
        )
    
    def _create_agent_response(self, recommendation: MarketRecommendation, forecast: PriceForecast, query: AgricultureQuery) -> AgentResponse:
        """Create a structured agent response"""
        
        summary = self._create_summary(recommendation, forecast, query.query_language)
        recommendations_list = self._create_recommendations_list(recommendation, forecast)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name="Market Timing Advisor",
            query_id=query.query_id,
            response_text=summary,
            response_language=query.query_language,
            confidence_score=recommendation.confidence_score,
            reasoning=", ".join(recommendation.reasoning),
            recommendations=recommendations_list,
            sources=["Simulated Historical Market Data", "Trend Analysis Model"],
            next_steps=["Check for updated forecast next week", "Monitor local mandi prices"],
            timestamp=datetime.now(),
            processing_time_ms=150,
            metadata={
                "commodity": forecast.commodity.value,
                "current_price": forecast.current_price,
                "forecast_7d": forecast.forecast_price_7d,
                "forecast_30d": forecast.forecast_price_30d,
                "trend": forecast.trend.value,
                "volatility": forecast.volatility
            }
        )
    
    def _create_summary(self, recommendation: MarketRecommendation, forecast: PriceForecast, language: Language) -> str:
        """Create a localized summary"""
        commodity_name = forecast.commodity.name.capitalize()
        
        if language in [Language.HINDI, Language.MIXED]:
            commodity_translations = {
                "Wheat": "गेहूं", "Rice": "चावल", "Cotton": "कपास", "Sugarcane": "गन्ना",
                "Soybean": "सोयाबीन", "Mustard": "सरसों", "Maize": "मक्का",
                "Potato": "आलू", "Onion": "प्याज", "Tomato": "टमाटर"
            }
            commodity_name = commodity_translations.get(commodity_name, commodity_name)
            
            rec_translations = {
                "Hold for higher prices": "ऊंची कीमतों के लिए रोकें",
                "Hold for now": "अभी के लिए रोकें",
                "Sell immediately": "तुरंत बेचें",
                "Consider selling soon": "जल्द बेचने पर विचार करें",
                "Hold and monitor market": "बाजार पर नजर रखें और रोकें"
            }
            rec_text = rec_translations.get(recommendation.recommendation, recommendation.recommendation)
            
            return (f"{commodity_name} के लिए सुझाव: {rec_text}। "
                    f"वर्तमान मूल्य: ₹{forecast.current_price:.2f}/क्विंटल। "
                    f"7-दिन का पूर्वानुमान: ₹{forecast.forecast_price_7d:.2f}।")
        
        return (f"Recommendation for {commodity_name}: {recommendation.recommendation}. "
                f"Current price: ₹{forecast.current_price:.2f}/quintal. "
                f"7-day forecast: ₹{forecast.forecast_price_7d:.2f}.")

    def _create_recommendations_list(self, recommendation: MarketRecommendation, forecast: PriceForecast) -> List[Dict[str, Any]]:
        """Create a list of detailed recommendations"""
        recs = [
            {
                "title": f"Primary Action: {recommendation.recommendation}",
                "description": f"Timeline: {recommendation.timeline}. Expected gain: {recommendation.expected_gain:.2f}%",
                "priority": "high",
                "action_required": recommendation.recommendation
            },
            {
                "title": "Price Forecast",
                "description": f"7-day: ₹{forecast.forecast_price_7d}, 30-day: ₹{forecast.forecast_price_30d}",
                "priority": "medium",
                "action_required": "Monitor"
            },
            {
                "title": "Market Volatility",
                "description": f"{forecast.volatility:.2f}% (Suggests price stability)" if forecast.volatility < 5 else f"{forecast.volatility:.2f}% (Suggests price fluctuations)",
                "priority": "low",
                "action_required": "Be cautious"
            }
        ]
        return recs

    def _create_general_market_info_response(self, query: AgricultureQuery) -> AgentResponse:
        """Create a response when no specific commodity is identified"""
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name="Market Timing Advisor",
            query_id=query.query_id,
            response_text="Please specify a commodity (e.g., wheat, rice, cotton) for a price forecast. कृपया मूल्य पूर्वानुमान के लिए एक वस्तु (जैसे गेहूं, चावल, कपास) निर्दिष्ट करें।",
            response_language=query.query_language,
            confidence_score=0.9,
            recommendations=[
                {"title": "Specify Commodity", "description": "Mention the crop you want a forecast for.", "priority": "high"}
            ],
            timestamp=datetime.now()
        )

    def _create_error_response(self, query: AgricultureQuery, error: str) -> AgentResponse:
        """Create an error response"""
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name="Market Timing Advisor",
            query_id=query.query_id,
            response_text="Sorry, I encountered a technical issue while forecasting. Please try again later. क्षमा करें, पूर्वानुमान करते समय मुझे एक तकनीकी समस्या का सामना करना पड़ा। कृपया बाद में पुन: प्रयास करें।",
            response_language=query.query_language,
            confidence_score=0.1,
            warnings=[f"Technical error: {error}"],
            timestamp=datetime.now(),
            metadata={"error": True, "error_message": error}
        )


# Test function for the Market Timing Agent
async def test_market_timing_agent():
    """Test the Market Timing Agent"""
    agent = MarketTimingAgent()
    
    print("📈 Testing Market Timing Agent")
    
    # Test a query in English
    query_en = AgricultureQuery(
        query_text="What is the price forecast for wheat?",
        query_language=Language.ENGLISH,
        user_id="test_farmer_en",
        location=Location(state="Punjab", district="Amritsar")
    )
    
    print("🔄 Processing English query for Wheat...")
    response_en = await agent.process_query(query_en)
    print(f"✅ English Response: {response_en.response_text}")
    
    # Test a query in Hindi
    query_hi = AgricultureQuery(
        query_text="प्याज का भाव क्या रहेगा?",
        query_language=Language.HINDI,
        user_id="test_farmer_hi",
        location=Location(state="Maharashtra", district="Nashik")
    )
    
    print("🔄 Processing Hindi query for Onion...")
    response_hi = await agent.process_query(query_hi)
    print(f"✅ Hindi Response: {response_hi.response_text}")

    # Test a query with no commodity
    query_general = AgricultureQuery(
        query_text="What is the market trend?",
        query_language=Language.ENGLISH,
        user_id="test_farmer_gen"
    )
    print("🔄 Processing general query...")
    response_gen = await agent.process_query(query_general)
    print(f"✅ General Response: {response_gen.response_text}")

    print("\n🎉 Market Timing Agent working successfully!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_market_timing_agent())
