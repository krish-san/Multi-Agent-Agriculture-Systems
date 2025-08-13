
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketIntegrationService:
    
    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.active_workflows = {}
        self.agent_states = {}
        
    def set_websocket_manager(self, manager):
        self.websocket_manager = manager
        
    async def notify_workflow_started(self, workflow_id: str, workflow_data: Dict[str, Any]):
        if not self.websocket_manager:
            return
            
        try:
            # Track workflow
            self.active_workflows[workflow_id] = {
                "id": workflow_id,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "steps_completed": 0,
                "total_steps": workflow_data.get("estimated_steps", 5),
                "current_step": "initializing",
                "input_data": workflow_data.get("input_data", {}),
                "metadata": workflow_data.get("metadata", {})
            }
            
            message = {
                "type": "workflow_update",
                "event": "workflow_started",
                "workflow_id": workflow_id,
                "status": "running",
                "current_step": "initializing",
                "progress": 0.0,
                "details": {
                    "started_at": self.active_workflows[workflow_id]["started_at"],
                    "estimated_steps": self.active_workflows[workflow_id]["total_steps"],
                    "input_summary": self._summarize_input(workflow_data.get("input_data", {}))
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.broadcast(message)
            logger.info(f"Broadcasted workflow start notification for {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting workflow start for {workflow_id}: {e}")
    
    async def notify_workflow_step(self, workflow_id: str, step_name: str, step_data: Dict[str, Any] = None):
        if not self.websocket_manager:
            return
            
        try:
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow["steps_completed"] += 1
                workflow["current_step"] = step_name
                workflow["progress"] = workflow["steps_completed"] / workflow["total_steps"]
                
                message = {
                    "type": "workflow_update",
                    "event": "step_completed",
                    "workflow_id": workflow_id,
                    "status": "running",
                    "current_step": step_name,
                    "progress": min(workflow["progress"], 1.0),
                    "details": {
                        "step_data": step_data or {},
                        "steps_completed": workflow["steps_completed"],
                        "total_steps": workflow["total_steps"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.websocket_manager.broadcast(message)
                logger.info(f"Broadcasted step completion for {workflow_id}: {step_name}")
                
        except Exception as e:
            logger.error(f"Error broadcasting workflow step for {workflow_id}: {e}")
    
    async def notify_workflow_completed(self, workflow_id: str, result: Dict[str, Any]):
        if not self.websocket_manager:
            return
            
        try:
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow["status"] = "completed"
                workflow["completed_at"] = datetime.now().isoformat()
                workflow["progress"] = 1.0
                workflow["result"] = result
                
                execution_time = None
                if "started_at" in workflow:
                    start_time = datetime.fromisoformat(workflow["started_at"])
                    execution_time = (datetime.now() - start_time).total_seconds()
                
                message = {
                    "type": "workflow_update",
                    "event": "workflow_completed",
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "current_step": "completed",
                    "progress": 1.0,
                    "details": {
                        "completed_at": workflow["completed_at"],
                        "execution_time": execution_time,
                        "result_summary": self._summarize_result(result),
                        "total_steps": workflow["steps_completed"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.websocket_manager.broadcast(message)
                logger.info(f"Broadcasted workflow completion for {workflow_id}")
                
                # Keep completed workflows for a while, then clean up
                asyncio.create_task(self._cleanup_workflow(workflow_id, delay=300))  # 5 minutes
                
        except Exception as e:
            logger.error(f"Error broadcasting workflow completion for {workflow_id}: {e}")
    
    async def notify_workflow_failed(self, workflow_id: str, error: str, error_details: Dict[str, Any] = None):
        if not self.websocket_manager:
            return
            
        try:
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow["status"] = "failed"
                workflow["failed_at"] = datetime.now().isoformat()
                workflow["error"] = error
                workflow["error_details"] = error_details or {}
                
                message = {
                    "type": "workflow_update",
                    "event": "workflow_failed",
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "current_step": workflow.get("current_step", "unknown"),
                    "progress": workflow.get("progress", 0.0),
                    "details": {
                        "failed_at": workflow["failed_at"],
                        "error": error,
                        "error_details": error_details or {},
                        "steps_completed": workflow.get("steps_completed", 0)
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.websocket_manager.broadcast(message)
                logger.info(f"Broadcasted workflow failure for {workflow_id}")
                
                # Clean up failed workflow after delay
                asyncio.create_task(self._cleanup_workflow(workflow_id, delay=600))  # 10 minutes
                
        except Exception as e:
            logger.error(f"Error broadcasting workflow failure for {workflow_id}: {e}")
    
    async def notify_agent_status_change(self, agent_id: str, old_status: str, new_status: str, details: Dict[str, Any] = None):
        if not self.websocket_manager:
            return
            
        try:
            # Update agent state tracking
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = {}
            
            self.agent_states[agent_id].update({
                "status": new_status,
                "last_status_change": datetime.now().isoformat(),
                "previous_status": old_status,
                "details": details or {}
            })
            
            message = {
                "type": "agent_update",
                "event": "status_changed",
                "agent_id": agent_id,
                "status": new_status,
                "previous_status": old_status,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.broadcast(message)
            logger.info(f"Broadcasted agent status change for {agent_id}: {old_status} -> {new_status}")
            
        except Exception as e:
            logger.error(f"Error broadcasting agent status change for {agent_id}: {e}")
    
    async def notify_system_event(self, event_type: str, message: str, level: str = "info", details: Dict[str, Any] = None):
        if not self.websocket_manager:
            return
            
        try:
            notification = {
                "type": "system_notification",
                "event_type": event_type,
                "message": message,
                "level": level,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket_manager.broadcast(notification)
            logger.info(f"Broadcasted system event: {event_type} - {message}")
            
        except Exception as e:
            logger.error(f"Error broadcasting system event {event_type}: {e}")
    
    def _summarize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        summary = {}
        
        if "text" in input_data:
            text = input_data["text"]
            summary["text_length"] = len(text) if isinstance(text, str) else 0
            summary["text_preview"] = text[:100] + "..." if isinstance(text, str) and len(text) > 100 else text
        
        if "metadata" in input_data:
            summary["metadata_keys"] = list(input_data["metadata"].keys()) if isinstance(input_data["metadata"], dict) else []
        
        summary["total_keys"] = len(input_data)
        return summary
    
    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        summary = {}
        
        if "status" in result:
            summary["status"] = result["status"]
        
        if "sentiment_score" in result:
            summary["sentiment_score"] = result["sentiment_score"]
        
        if "routing_decision" in result:
            summary["routing_decision"] = result["routing_decision"]
        
        if "completed_steps" in result:
            summary["steps_executed"] = len(result["completed_steps"])
        
        summary["result_keys"] = len(result)
        return summary
    
    async def _cleanup_workflow(self, workflow_id: str, delay: int = 300):
        await asyncio.sleep(delay)
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
            logger.info(f"Cleaned up workflow data for {workflow_id}")
    
    def get_system_status(self) -> Dict[str, Any]:
        active_workflows = [w for w in self.active_workflows.values() if w.get("status") in ["running", "pending"]]
        completed_workflows = [w for w in self.active_workflows.values() if w.get("status") == "completed"]
        failed_workflows = [w for w in self.active_workflows.values() if w.get("status") == "failed"]
        
        active_agents = [a for a in self.agent_states.values() if a.get("status") in ["active", "busy"]]
        
        return {
            "workflows": {
                "total": len(self.active_workflows),
                "active": len(active_workflows),
                "completed": len(completed_workflows),
                "failed": len(failed_workflows)
            },
            "agents": {
                "total": len(self.agent_states),
                "active": len(active_agents)
            },
            "websocket_connections": len(self.websocket_manager.active_connections) if self.websocket_manager else 0
        }


# Global instance
integration_service = WebSocketIntegrationService()
