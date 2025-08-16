"""
FastAPI WebSocket Endpoints for the Agriculture Systems Dashboard
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AgentWeaver WebSocket API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager for the main dashboard
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_count = 0
        
    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        connection_id = str(uuid4())
        self.active_connections[connection_id] = websocket
        self.connection_count += 1
        logger.info(f"New connection {connection_id}. Total connections: {self.connection_count}")
        return connection_id
        
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            self.connection_count -= 1
            logger.info(f"Connection {connection_id} closed. Total connections: {self.connection_count}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_text(json.dumps(message))
            
    async def broadcast(self, message: dict):
        logger.info(f"Broadcasting to {len(self.active_connections)} connections")
        for connection in self.active_connections.values():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message: {e}")


# Create connection managers
dashboard_manager = ConnectionManager()
chat_manager = ConnectionManager()


# Utility functions
def timestamp() -> str:
    """Return current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = await dashboard_manager.connect(websocket)
    
    # Send a welcome message
    await dashboard_manager.send_personal_message(
        {
            "type": "system_notification",
            "event_type": "connection_established",
            "message": "Connected to dashboard updates",
            "level": "info",
            "timestamp": timestamp(),
            "details": {
                "connection_id": connection_id,
                "active_connections": dashboard_manager.connection_count
            }
        },
        connection_id
    )
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle ping messages for connection heartbeat
                if message.get("type") == "ping":
                    await dashboard_manager.send_personal_message(
                        {
                            "type": "pong",
                            "timestamp": timestamp()
                        },
                        connection_id
                    )
                
                # Handle other message types as needed
                
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON: {data}")
                
    except WebSocketDisconnect:
        dashboard_manager.disconnect(connection_id)
        

@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    connection_id = await chat_manager.connect(websocket)
    
    # Send a welcome message
    await chat_manager.send_personal_message(
        {
            "type": "chat_message",
            "message_id": f"welcome-{uuid4()}",
            "content": "Hello! I'm your AgriHelper assistant. How can I help you today?",
            "sender": "bot",
            "timestamp": timestamp(),
            "options": [
                {"text": "🌦️ Weather Forecast", "action": "weather"},
                {"text": "🐛 Pest Control", "action": "pests"},
                {"text": "💰 Market Prices", "action": "prices"},
                {"text": "🌱 Crop Suggestions", "action": "crops"}
            ]
        },
        connection_id
    )
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "chat_message" and message.get("content"):
                    user_content = message["content"]
                    logger.info(f"Received chat message: {user_content}")
                    
                    # Echo back the received message as user message for confirmation
                    await chat_manager.send_personal_message(
                        {
                            "type": "chat_message",
                            "message_id": f"user-{uuid4()}",
                            "content": user_content,
                            "sender": "user",
                            "timestamp": timestamp()
                        },
                        connection_id
                    )
                    
                    # Send typing indicator
                    await chat_manager.send_personal_message(
                        {
                            "type": "chat_typing",
                            "timestamp": timestamp()
                        },
                        connection_id
                    )
                    
                    # Simulate processing delay
                    await asyncio.sleep(1.5)
                    
                    # Generate response based on user input
                    response, options = generate_bot_response(user_content)
                    
                    # Send the bot response
                    await chat_manager.send_personal_message(
                        {
                            "type": "chat_message",
                            "message_id": f"bot-{uuid4()}",
                            "content": response,
                            "sender": "bot",
                            "timestamp": timestamp(),
                            "options": options
                        },
                        connection_id
                    )
                    
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON: {data}")
                
    except WebSocketDisconnect:
        chat_manager.disconnect(connection_id)


def generate_bot_response(user_input: str) -> tuple[str, Optional[List[Dict[str, str]]]]:
    """
    Generate a response based on user input
    Returns a tuple of (response_text, quick_options)
    """
    user_input = user_input.lower()
    
    # Simple keyword matching for responses
    if "weather" in user_input:
        return (
            "Based on your location, our weather forecast shows clear skies for the next 3 days with a high of 78°F and low of 62°F. Perfect for crop maintenance! There's a 20% chance of light rain on Friday.",
            [
                {"text": "🗓️ Weekly Forecast", "action": "weekly forecast"},
                {"text": "☔ Rain Probability", "action": "rain chances"},
                {"text": "🌡️ Temperature Trends", "action": "temperature"}
            ]
        )
    elif "weekly forecast" in user_input:
        return (
            "Here's your 7-day forecast:\nMonday: 78°F, Sunny\nTuesday: 75°F, Partly Cloudy\nWednesday: 76°F, Sunny\nThursday: 79°F, Sunny\nFriday: 74°F, 20% Rain\nSaturday: 72°F, 40% Rain\nSunday: 75°F, Partly Cloudy",
            None
        )
    elif "pest" in user_input or "insect" in user_input:
        return (
            "I detect you're asking about pest control. Based on recent reports in your area, farmers are seeing increased aphid activity on crops. Would you like information about organic or chemical treatments?",
            [
                {"text": "🌿 Organic Solutions", "action": "organic pest control"},
                {"text": "🧪 Chemical Options", "action": "chemical pest control"},
                {"text": "🔍 Identify Pests", "action": "identify pests"}
            ]
        )
    elif "crop" in user_input or "plant" in user_input:
        return (
            "Based on your soil analysis (pH 6.8, loamy texture) and current season, we recommend planting wheat, barley, or pulse crops for maximum yield. Your location has received sufficient rainfall for germination.",
            [
                {"text": "🌾 Seasonal Crops", "action": "seasonal crops"},
                {"text": "💧 Water Requirements", "action": "crop water needs"},
                {"text": "🌿 Crop Rotation", "action": "crop rotation"}
            ]
        )
    elif "market" in user_input or "price" in user_input:
        return (
            "Current market prices show: Corn: $4.85/bu (+2.1% weekly), Soybeans: $13.20/bu (+1.5% weekly), Wheat: $6.75/bu (-0.5% weekly). Organic produce is trading at a 15-25% premium over conventional.",
            [
                {"text": "📊 Price Trends", "action": "market trends"},
                {"text": "📈 Price Forecasts", "action": "price forecast"},
                {"text": "🚚 Distribution Channels", "action": "distribution"}
            ]
        )
    elif "hello" in user_input or "hi" in user_input:
        return (
            "Hello! I'm your AgriHelper assistant. I can provide information on weather forecasts, pest control, crop recommendations, and market prices tailored to your farm's location and conditions.",
            [
                {"text": "🌦️ Weather", "action": "weather"},
                {"text": "🐛 Pests", "action": "pests"},
                {"text": "🌱 Crops", "action": "crops"}
            ]
        )
    else:
        return (
            "I'll analyze your question and find the most relevant information. To provide better assistance, would you like me to consider your farm's specific soil type, location, and current crops in my response?",
            [
                {"text": "❓ Ask Different Question", "action": "help"},
                {"text": "👨‍🌾 Talk to Expert", "action": "expert"}
            ]
        )


# Add a route to simulate system events for testing
@app.get("/simulate/workflow-update")
async def simulate_workflow_update():
    """Simulate a workflow update event"""
    await dashboard_manager.broadcast({
        "type": "workflow_update",
        "event": "step_completed",
        "workflow_id": f"wf-{uuid4()}",
        "status": "running",
        "current_step": "Data Processing",
        "progress": 0.5,
        "timestamp": timestamp(),
        "details": {
            "step_name": "Data Processing",
            "step_id": f"step-{uuid4()}",
            "duration": 1.5,
            "next_step": "Analysis"
        }
    })
    return {"success": True, "message": "Workflow update sent"}


@app.get("/simulate/agent-update")
async def simulate_agent_update():
    """Simulate an agent status update event"""
    await dashboard_manager.broadcast({
        "type": "agent_update",
        "event": "status_changed",
        "agent_id": f"agent-{uuid4()}", 
        "status": "busy",
        "previous_status": "idle",
        "timestamp": timestamp(),
        "details": {
            "current_task": "Processing weather data",
            "cpu_usage": 45.2,
            "memory_usage": 128.5,
            "estimated_completion": (datetime.utcnow().timestamp() + 120) * 1000
        }
    })
    return {"success": True, "message": "Agent update sent"}


@app.get("/simulate/notification")
async def simulate_notification():
    """Simulate a system notification"""
    await dashboard_manager.broadcast({
        "type": "system_notification",
        "event_type": "resource_warning",
        "message": "CPU usage exceeding threshold on worker node 3",
        "level": "warning",
        "timestamp": timestamp(),
        "details": {
            "resource": "CPU",
            "value": 87.5,
            "threshold": 80.0,
            "node": "worker-3"
        }
    })
    return {"success": True, "message": "Notification sent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("websocket_server:app", host="0.0.0.0", port=8000, reload=True)
