
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..core.models import (
    AgentState, Task, Message, WorkflowState, SystemState,
    TaskStatus, TaskPriority, MessageType, MessagePriority, 
    AgentCapability, AgentStatus
)

logger = logging.getLogger(__name__)


class SupervisorNode:
    
    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        self.checkpointer = checkpointer or MemorySaver()
        self.agent_registry: Dict[str, AgentState] = {}
        self.task_queue: List[Task] = []
        self.system_state = SystemState()
        self._setup_supervisor_graph()
        
    def _setup_supervisor_graph(self):
        # Create the graph with our SystemState
        graph = StateGraph(dict)
        
        # Add supervisor nodes
        graph.add_node("register_agent", self._register_agent_node)
        graph.add_node("unregister_agent", self._unregister_agent_node)
        graph.add_node("assign_task", self._assign_task_node)
        graph.add_node("monitor_health", self._monitor_health_node)
        graph.add_node("process_supervisor_message", self._process_supervisor_message_node)
        
        # Define routing function
        def route_message(state: Dict[str, Any]) -> str:
            message = state.get("message")
            if not message:
                return "monitor_health"  # Default action
                
            message_type = message.get("type", "health_check")
            
            if message_type == "register_agent":
                return "register_agent"
            elif message_type == "unregister_agent":
                return "unregister_agent"
            elif message_type == "assign_task":
                return "assign_task"
            elif message_type == "health_check":
                return "monitor_health"
            else:
                return "monitor_health"  # Default
                
        # Add edges with conditional routing
        graph.add_edge(START, "process_supervisor_message")
        graph.add_conditional_edges(
            "process_supervisor_message",
            route_message,
            {
                "register_agent": "register_agent",
                "unregister_agent": "unregister_agent", 
                "assign_task": "assign_task",
                "monitor_health": "monitor_health"
            }
        )
        graph.add_edge("register_agent", END)
        graph.add_edge("unregister_agent", END)
        graph.add_edge("assign_task", END)
        graph.add_edge("monitor_health", END)
        
        # Compile the graph
        self.supervisor_graph = graph.compile(checkpointer=self.checkpointer)
        
    def _register_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            agent_data = state.get("agent_to_register")
            if not agent_data:
                # Create default agent data if none provided
                agent_data = {
                    "name": "Unknown Agent",
                    "capabilities": []
                }
                
            # Create AgentState from provided data
            agent = AgentState(
                agent_id=agent_data.get("agent_id", str(uuid.uuid4())),
                name=agent_data.get("name", "Unknown Agent"),
                capabilities=agent_data.get("capabilities", []),
                status=AgentStatus.AVAILABLE,
                current_task_id=None
            )
            
            # Register the agent
            self.agent_registry[agent.agent_id] = agent
            
            # Update system state
            if "system_state" not in state:
                state["system_state"] = {}
            state["system_state"]["total_agents"] = len(self.agent_registry)
            state["system_state"]["available_agents"] = len([
                a for a in self.agent_registry.values() 
                if a.status == AgentStatus.AVAILABLE
            ])
            
            logger.info(f"Agent {agent.agent_id} ({agent.name}) registered successfully")
            state["registration_result"] = {
                "success": True,
                "agent_id": agent.agent_id,
                "message": f"Agent {agent.name} registered successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to register agent: {str(e)}")
            state["registration_result"] = {
                "success": False,
                "error": str(e)
            }
            
        return state
        
    def _unregister_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            agent_id = state.get("agent_id_to_unregister")
            if not agent_id:
                logger.error("No agent ID provided for unregistration")
                return state
                
            if agent_id in self.agent_registry:
                agent = self.agent_registry[agent_id]
                del self.agent_registry[agent_id]
                
                # Update system state
                if "system_state" not in state:
                    state["system_state"] = {}
                state["system_state"]["total_agents"] = len(self.agent_registry)
                state["system_state"]["available_agents"] = len([
                    a for a in self.agent_registry.values() 
                    if a.status == AgentStatus.AVAILABLE
                ])
                
                logger.info(f"Agent {agent_id} ({agent.name}) unregistered successfully")
                state["unregistration_result"] = {
                    "success": True,
                    "agent_id": agent_id,
                    "message": f"Agent {agent.name} unregistered successfully"
                }
            else:
                logger.warning(f"Agent {agent_id} not found in registry")
                state["unregistration_result"] = {
                    "success": False,
                    "error": f"Agent {agent_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Failed to unregister agent: {str(e)}")
            state["unregistration_result"] = {
                "success": False,
                "error": str(e)
            }
            
        return state
        
    def _assign_task_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            task_data = state.get("task_to_assign")
            if not task_data:
                logger.error("No task data provided for assignment")
                return state
                
            # Create Task from provided data
            task = Task(
                task_id=task_data.get("task_id", str(uuid.uuid4())),
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description", ""),
                required_capabilities=task_data.get("required_capabilities", []),
                priority=TaskPriority(task_data.get("priority", "medium")),
                status=TaskStatus.PENDING
            )
            
            # Find suitable agent
            suitable_agent = self._find_suitable_agent(task)
            
            if suitable_agent:
                # Assign task to agent
                suitable_agent.status = AgentStatus.BUSY
                suitable_agent.current_task_id = task.task_id
                task.assigned_agent_id = suitable_agent.agent_id
                task.status = TaskStatus.IN_PROGRESS
                task.assign_task(suitable_agent.agent_id)
                
                # Update system state
                if "system_state" not in state:
                    state["system_state"] = {}
                state["system_state"]["available_agents"] = len([
                    a for a in self.agent_registry.values() 
                    if a.status == AgentStatus.AVAILABLE
                ])
                state["system_state"]["busy_agents"] = len([
                    a for a in self.agent_registry.values() 
                    if a.status == AgentStatus.BUSY
                ])
                
                logger.info(f"Task {task.task_id} assigned to agent {suitable_agent.agent_id}")
                state["assignment_result"] = {
                    "success": True,
                    "task_id": task.task_id,
                    "agent_id": suitable_agent.agent_id,
                    "message": f"Task assigned to agent {suitable_agent.name}"
                }
            else:
                # No suitable agent available, add to queue
                self.task_queue.append(task)
                logger.info(f"Task {task.task_id} added to queue - no suitable agent available")
                state["assignment_result"] = {
                    "success": False,
                    "task_id": task.task_id,
                    "message": "No suitable agent available, task queued"
                }
                
        except Exception as e:
            logger.error(f"Failed to assign task: {str(e)}")
            state["assignment_result"] = {
                "success": False,
                "error": str(e)
            }
            
        return state
        
    def _monitor_health_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "total_agents": len(self.agent_registry),
                "available_agents": 0,
                "busy_agents": 0,
                "offline_agents": 0,
                "queued_tasks": len(self.task_queue),
                "agent_details": []
            }
            
            # Check each agent's health
            for agent in self.agent_registry.values():
                if agent.status == AgentStatus.AVAILABLE:
                    health_report["available_agents"] += 1
                elif agent.status == AgentStatus.BUSY:
                    health_report["busy_agents"] += 1
                else:
                    health_report["offline_agents"] += 1
                    
                agent_detail = {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "status": agent.status.value,
                    "capabilities": [cap.value for cap in agent.capabilities],
                    "current_task": agent.current_task_id,
                    "last_updated": agent.last_updated.isoformat()
                }
                health_report["agent_details"].append(agent_detail)
                
            # Update system state
            if "system_state" not in state:
                state["system_state"] = {}
            state["system_state"].update({
                "total_agents": health_report["total_agents"],
                "available_agents": health_report["available_agents"],
                "busy_agents": health_report["busy_agents"],
                "queued_tasks": health_report["queued_tasks"]
            })
            
            state["health_report"] = health_report
            logger.info(f"Health check completed: {health_report['available_agents']} available, "
                       f"{health_report['busy_agents']} busy, {health_report['queued_tasks']} queued tasks")
                       
        except Exception as e:
            logger.error(f"Health monitoring failed: {str(e)}")
            state["health_report"] = {"error": str(e)}
            
        return state
        
    def _process_supervisor_message_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            message_data = state.get("message")
            if not message_data:
                # No message to process, return state as-is
                return state
                
            message_type = message_data.get("type", "general")
            
            # Route message based on type and set up data for next node
            if message_type == "register_agent":
                state["agent_to_register"] = message_data.get("content")
            elif message_type == "unregister_agent":
                content = message_data.get("content", {})
                if isinstance(content, dict):
                    state["agent_id_to_unregister"] = content.get("agent_id")
                else:
                    state["agent_id_to_unregister"] = content
            elif message_type == "assign_task":
                state["task_to_assign"] = message_data.get("content")
            elif message_type == "health_check":
                # Health check will be processed by monitor_health_node
                pass
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
            logger.info(f"Processed supervisor message of type: {message_type}")
            
        except Exception as e:
            logger.error(f"Failed to process supervisor message: {str(e)}")
            state["message_processing_error"] = str(e)
            
        return state
        
    def _find_suitable_agent(self, task: Task) -> Optional[AgentState]:
        for agent in self.agent_registry.values():
            if (agent.status == AgentStatus.AVAILABLE and 
                self._agent_has_required_capabilities(agent, task.required_capabilities)):
                return agent
        return None
        
    def _agent_has_required_capabilities(self, agent: AgentState, 
                                       required_capabilities: List[AgentCapability]) -> bool:
        if not required_capabilities:
            return True
            
        agent_capabilities = set(agent.capabilities)
        required_set = set(required_capabilities)
        return required_set.issubset(agent_capabilities)
        
    # Public interface methods
    
    def register_agent(self, agent_data: Dict[str, Any], thread_id: str = "supervisor") -> Dict[str, Any]:
        initial_state = {
            "message": {
                "type": "register_agent",
                "content": agent_data
            }
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        result = self.supervisor_graph.invoke(initial_state, config)
        
        return result.get("registration_result", {"success": False, "error": "Unknown error"})
        
    def unregister_agent(self, agent_id: str, thread_id: str = "supervisor") -> Dict[str, Any]:
        initial_state = {
            "message": {
                "type": "unregister_agent",
                "content": {"agent_id": agent_id}
            }
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        result = self.supervisor_graph.invoke(initial_state, config)
        
        return result.get("unregistration_result", {"success": False, "error": "Unknown error"})
        
    def assign_task(self, task_data: Dict[str, Any], thread_id: str = "supervisor") -> Dict[str, Any]:
        initial_state = {
            "message": {
                "type": "assign_task",
                "content": task_data
            }
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        result = self.supervisor_graph.invoke(initial_state, config)
        
        return result.get("assignment_result", {"success": False, "error": "Unknown error"})
        
    def get_health_report(self, thread_id: str = "supervisor") -> Dict[str, Any]:
        initial_state = {
            "message": {
                "type": "health_check",
                "content": {}
            }
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        result = self.supervisor_graph.invoke(initial_state, config)
        
        return result.get("health_report", {"error": "Health check failed"})
        
    def get_agent_registry(self) -> Dict[str, AgentState]:
        return self.agent_registry.copy()
        
    def get_task_queue(self) -> List[Task]:
        return self.task_queue.copy()
        
    def mark_task_complete(self, task_id: str, agent_id: str) -> bool:
        try:
            if agent_id in self.agent_registry:
                agent = self.agent_registry[agent_id]
                if agent.current_task_id == task_id:
                    agent.status = AgentStatus.AVAILABLE
                    agent.current_task_id = None
                    agent.update_performance(success=True)
                    logger.info(f"Task {task_id} completed by agent {agent_id}")
                    
                    # Try to assign queued tasks
                    self._process_queued_tasks()
                    return True
                    
            logger.warning(f"Task {task_id} completion failed - agent {agent_id} not found or task mismatch")
            return False
            
        except Exception as e:
            logger.error(f"Failed to mark task complete: {str(e)}")
            return False
            
    def _process_queued_tasks(self):
        tasks_to_remove = []
        
        for i, task in enumerate(self.task_queue):
            suitable_agent = self._find_suitable_agent(task)
            if suitable_agent:
                # Assign the task
                suitable_agent.status = AgentStatus.BUSY
                suitable_agent.current_task_id = task.task_id
                task.assigned_agent_id = suitable_agent.agent_id
                task.status = TaskStatus.IN_PROGRESS
                task.assign_task(suitable_agent.agent_id)
                
                tasks_to_remove.append(i)
                logger.info(f"Queued task {task.task_id} assigned to agent {suitable_agent.agent_id}")
                
        # Remove assigned tasks from queue (in reverse order to maintain indices)
        for i in reversed(tasks_to_remove):
            del self.task_queue[i]
    
    @property
    def supervisor_id(self) -> str:
        if not hasattr(self, '_supervisor_id'):
            self._supervisor_id = str(uuid.uuid4())
        return self._supervisor_id
    
    def monitor_agents(self) -> Dict[str, Any]:
        try:
            monitoring_report = {
                'timestamp': datetime.utcnow().isoformat(),
                'supervisor_id': self.supervisor_id,
                'total_agents': len(self.agent_registry),
                'agents_by_status': {},
                'task_queue_length': len(self.task_queue),
                'agent_details': {}
            }
            
            # Count agents by status
            status_counts = {}
            for agent in self.agent_registry.values():
                status = agent.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Add detailed agent information
                monitoring_report['agent_details'][agent.agent_id] = {
                    'name': agent.name,
                    'status': status,
                    'current_task': agent.current_task_id,
                    'capabilities': [cap.value for cap in agent.capabilities],
                    'last_activity': agent.last_activity.isoformat() if agent.last_activity else None,
                    'health_check_passed': agent.health_check_passed,
                    'tasks_completed': agent.tasks_completed,
                    'tasks_failed': agent.tasks_failed
                }
            
            monitoring_report['agents_by_status'] = status_counts
            
            # Check for unhealthy agents
            unhealthy_agents = []
            for agent in self.agent_registry.values():
                if not agent.health_check_passed or agent.status == AgentStatus.ERROR:
                    unhealthy_agents.append(agent.agent_id)
            
            monitoring_report['unhealthy_agents'] = unhealthy_agents
            monitoring_report['health_issues'] = len(unhealthy_agents) > 0
            
            logger.info(f"Agent monitoring completed: {len(self.agent_registry)} agents, {len(unhealthy_agents)} health issues")
            
            return monitoring_report
            
        except Exception as e:
            logger.error(f"Failed to monitor agents: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'supervisor_id': self.supervisor_id
            }
    
    def get_supervisor_status(self) -> Dict[str, Any]:
        try:
            return {
                'supervisor_id': self.supervisor_id,
                'status': 'active',
                'timestamp': datetime.utcnow().isoformat(),
                'registered_agents': len(self.agent_registry),
                'queued_tasks': len(self.task_queue),
                'graph_compiled': self.supervisor_graph is not None,
                'system_state': {
                    'workflow_id': self.system_state.workflow_id,
                    'current_step': self.system_state.current_step,
                    'total_steps': self.system_state.total_steps
                },
                'capabilities': [
                    'agent_registration',
                    'task_assignment', 
                    'health_monitoring',
                    'message_processing'
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get supervisor status: {str(e)}")
            return {
                'supervisor_id': self.supervisor_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def handle_failure(self, agent_id: str, task_id: str = None, failure_reason: str = None) -> bool:
        try:
            logger.warning(f"Handling failure for agent {agent_id}, task {task_id}: {failure_reason}")
            
            # Mark agent as having an error
            if agent_id in self.agent_registry:
                agent = self.agent_registry[agent_id]
                agent.status = AgentStatus.ERROR
                agent.error_message = failure_reason or "Agent failure detected"
                agent.health_check_passed = False
                agent.last_updated = datetime.utcnow()
                
                # If the agent was working on a task, handle task reassignment
                if task_id or agent.current_task_id:
                    failed_task_id = task_id or agent.current_task_id
                    self._handle_task_reassignment(failed_task_id, agent_id)
                
                # Clear the agent's current task
                agent.current_task_id = None
                
                logger.info(f"Agent {agent_id} marked as failed and task reassignment initiated")
                return True
            else:
                logger.error(f"Cannot handle failure: Agent {agent_id} not found in registry")
                return False
                
        except Exception as e:
            logger.error(f"Failed to handle agent failure: {str(e)}")
            return False
    
    def _handle_task_reassignment(self, task_id: str, failed_agent_id: str) -> bool:
        try:
            # Create a mock task for reassignment (in a real system, this would come from task storage)
            reassignment_task = Task(
                task_id=task_id,
                title=f"Reassigned Task {task_id}",
                description=f"Task reassigned due to agent {failed_agent_id} failure",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH  # High priority for reassigned tasks
            )
            
            # Try to find another suitable agent
            suitable_agent = self._find_suitable_agent(reassignment_task)
            
            if suitable_agent:
                # Assign to the new agent
                suitable_agent.status = AgentStatus.BUSY
                suitable_agent.current_task_id = task_id
                reassignment_task.assigned_agent_id = suitable_agent.agent_id
                reassignment_task.status = TaskStatus.IN_PROGRESS
                
                logger.info(f"Task {task_id} reassigned from {failed_agent_id} to {suitable_agent.agent_id}")
                return True
            else:
                # Add to queue for later assignment
                self.task_queue.append(reassignment_task)
                logger.warning(f"Task {task_id} queued for reassignment - no suitable agent available")
                return True
                
        except Exception as e:
            logger.error(f"Failed to reassign task {task_id}: {str(e)}")
            return False
