
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..core.models import AgentState, AgentCapability, AgentStatus, Task, TaskStatus


logger = logging.getLogger(__name__)


class BaseWorkerAgent(ABC):
    
    def __init__(self, name: str, capabilities: List[AgentCapability], agent_type: str = "worker"):
        self.agent_state = AgentState(
            name=name,
            agent_type=agent_type,
            capabilities=capabilities,
            status=AgentStatus.AVAILABLE
        )
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @property
    def agent_id(self) -> str:
        return self.agent_state.agent_id
    
    @property
    def name(self) -> str:
        return self.agent_state.name
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return self.agent_state.capabilities
    
    @property
    def status(self) -> AgentStatus:
        return self.agent_state.status
    
    @abstractmethod
    def execute(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def can_handle_task(self, task: Task) -> bool:
        # Check if any of the task's required capabilities match this agent's capabilities
        if not task.required_capabilities:
            return True  # If no specific capabilities required, any agent can handle it
        
        return any(cap in self.capabilities for cap in task.required_capabilities)
    
    def start_task(self, task: Task) -> None:
        self.agent_state.status = AgentStatus.BUSY
        self.agent_state.current_task_id = task.task_id
        self.agent_state.last_activity = datetime.utcnow()
        self.agent_state.last_updated = datetime.utcnow()
        
        self.logger.info(f"Agent {self.name} starting task {task.task_id}: {task.title}")
    
    def complete_task(self, task: Task, execution_time: float = 0.0, success: bool = True) -> None:
        self.agent_state.status = AgentStatus.AVAILABLE
        self.agent_state.current_task_id = None
        # Note: update_performance method would need to be added to AgentState model
        
        status_msg = "completed successfully" if success else "failed"
        self.logger.info(f"Agent {self.name} {status_msg} task {task.task_id} in {execution_time:.2f}s")
    
    def set_error(self, error_message: str) -> None:
        self.agent_state.status = AgentStatus.ERROR
        self.agent_state.error_message = error_message
        self.agent_state.health_check_passed = False
        self.agent_state.last_updated = datetime.utcnow()
        
        self.logger.error(f"Agent {self.name} error: {error_message}")
    
    def reset_error(self) -> None:
        self.agent_state.status = AgentStatus.AVAILABLE
        self.agent_state.error_message = None
        self.agent_state.health_check_passed = True
        self.agent_state.last_updated = datetime.utcnow()
        
        self.logger.info(f"Agent {self.name} error status reset")
    
    def process_task(self, task: Task, context: Dict[str, Any] = None) -> Dict[str, Any]:
        if context is None:
            context = {}
        
        try:
            self.start_task(task)
            start_time = datetime.utcnow()
            
            # Execute the task
            result = self.execute(task, context)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Mark task as complete
            self.complete_task(task, execution_time, success=True)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() if 'start_time' in locals() else 0.0
            self.complete_task(task, execution_time, success=False)
            self.set_error(str(e))
            raise
    
    def send_message(self, recipient_id: str, message_content: Dict[str, Any], 
                    subject: str = "Agent Communication") -> bool:
        try:
            # This would integrate with the communication system
            # For now, we'll log the message
            self.logger.info(f"Agent {self.name} sending message to {recipient_id}: {subject}")
            self.logger.debug(f"Message content: {message_content}")
            
            # Update last activity
            self.agent_state.last_activity = datetime.utcnow()
            self.agent_state.last_updated = datetime.utcnow()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def update_status(self, status: AgentStatus, message: str = None) -> None:
        old_status = self.agent_state.status
        self.agent_state.status = status
        self.agent_state.last_updated = datetime.utcnow()
        
        if message:
            self.agent_state.context['status_message'] = message
        
        self.logger.info(f"Agent {self.name} status changed from {old_status} to {status}")
        if message:
            self.logger.info(f"Status message: {message}")
    
    def health_check(self) -> bool:
        try:
            # Basic health check - override in subclasses for specific checks
            is_healthy = (
                self.agent_state.status != AgentStatus.ERROR and
                self.agent_state.status != AgentStatus.OFFLINE
            )
            
            self.agent_state.health_check_passed = is_healthy
            self.agent_state.last_updated = datetime.utcnow()
            
            return is_healthy
            
        except Exception as e:
            self.logger.error(f"Health check failed for agent {self.name}: {str(e)}")
            self.set_error(f"Health check failed: {str(e)}")
            return False
    
    def get_state(self) -> AgentState:
        return self.agent_state.copy(deep=True)
    
    def update_context(self, context: Dict[str, Any]) -> None:
        self.agent_state.context.update(context)
        self.agent_state.last_updated = datetime.utcnow()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', id='{self.agent_id}', status='{self.status}')"
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"id='{self.agent_id}', "
            f"status='{self.status}', "
            f"capabilities={[cap.value for cap in self.capabilities]}"
            f")"
        )
