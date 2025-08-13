
import asyncio
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Store connection metadata
        connection_data = {
            "connected_at": datetime.now().isoformat(),
            "client_info": client_info or {},
            "messages_sent": 0
        }
        self.connection_info[websocket] = connection_data
        
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self._send_to_connection(websocket, {
            "type": "connection_established",
            "message": "Connected to AgentWeaver real-time updates",
            "timestamp": datetime.now().isoformat(),
            "connection_id": id(websocket)
        })
    
    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_info:
            connection_data = self.connection_info.pop(websocket)
            logger.info(f"WebSocket disconnected. Connection was active for {connection_data.get('connected_at')}. "
                       f"Total connections: {len(self.active_connections)}")
    
    async def disconnect_all(self):
        for websocket in self.active_connections.copy():
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket connection: {e}")
        
        self.active_connections.clear()
        self.connection_info.clear()
        logger.info("All WebSocket connections closed")
    
    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            logger.debug("No active WebSocket connections to broadcast to")
            return
        
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Send to all connections concurrently
        tasks = []
        for websocket in self.active_connections.copy():
            tasks.append(self._send_to_connection(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f"Broadcast message sent to {len(tasks)} connections")
    
    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]):
        if websocket in self.active_connections:
            await self._send_to_connection(websocket, message)
    
    async def _send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        try:
            # Check if connection is still active
            if websocket not in self.active_connections:
                return
                
            await websocket.send_text(json.dumps(message))
            
            # Update connection stats
            if websocket in self.connection_info:
                self.connection_info[websocket]["messages_sent"] += 1
                
        except WebSocketDisconnect:
            logger.debug("WebSocket disconnected during message send")
            await self.disconnect(websocket)
        except Exception as e:
            logger.warning(f"Error sending WebSocket message, disconnecting client: {e}")
            await self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        total_messages = sum(
            info.get("messages_sent", 0) 
            for info in self.connection_info.values()
        )
        
        return {
            "active_connections": len(self.active_connections),
            "total_messages_sent": total_messages,
            "connection_details": [
                {
                    "connection_id": id(ws),
                    "connected_at": info.get("connected_at"),
                    "messages_sent": info.get("messages_sent", 0),
                    "client_info": info.get("client_info", {})
                }
                for ws, info in self.connection_info.items()
            ]
        }
    
    async def send_agent_update(self, agent_id: str, status: str, details: Dict[str, Any] = None):
        message = {
            "type": "agent_update",
            "agent_id": agent_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_workflow_update(self, workflow_id: str, status: str, step: str = None, details: Dict[str, Any] = None):
        message = {
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "status": status,
            "current_step": step,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_system_notification(self, notification_type: str, message: str, level: str = "info"):
        notification = {
            "type": "system_notification",
            "notification_type": notification_type,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(notification)
