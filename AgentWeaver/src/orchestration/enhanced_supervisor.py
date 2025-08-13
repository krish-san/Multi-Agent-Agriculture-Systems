
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..core.models import (
    AgentState, Task, Message, WorkflowState, SystemState,
    TaskStatus, TaskPriority, MessageType, MessagePriority, 
    AgentCapability, AgentStatus
)
from ..agents import (
    BaseWorkerAgent,
    TextAnalysisAgent,
    APIInteractionAgent,
    DataProcessingAgent
)

logger = logging.getLogger(__name__)


class EnhancedSupervisor:
    
    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        self.checkpointer = checkpointer or MemorySaver()
        self.agent_registry: Dict[str, AgentState] = {}
        self.worker_agents: Dict[str, BaseWorkerAgent] = {}
        self.task_queue: List[Task] = []
        self.system_state = SystemState()
        self._setup_enhanced_graph()
        
        logger.info("Enhanced Supervisor initialized")
    
    def _setup_enhanced_graph(self):
        # Create the graph with enhanced state
        graph = StateGraph(dict)
        
        # Add supervisor nodes
        graph.add_node("supervisor", self._supervisor_dispatch_node)
        graph.add_node("process_task_result", self._process_task_result_node)
        
        # Add worker agent nodes
        graph.add_node("text_analysis_worker", self._text_analysis_worker_node)
        graph.add_node("api_interaction_worker", self._api_interaction_worker_node)
        graph.add_node("data_processing_worker", self._data_processing_worker_node)
        
        # Define routing function for task dispatch
        def route_to_worker(state: Dict[str, Any]) -> str:
            next_agent = state.get("next_agent")
            
            if next_agent == "text_analysis":
                return "text_analysis_worker"
            elif next_agent == "api_interaction":
                return "api_interaction_worker"
            elif next_agent == "data_processing":
                return "data_processing_worker"
            elif next_agent == "process_result":
                return "process_task_result"
            else:
                return END  # End if no more work to do
        
        # Add edges
        graph.add_edge(START, "supervisor")
        
        # Conditional edges from supervisor to workers
        graph.add_conditional_edges(
            "supervisor",
            route_to_worker,
            {
                "text_analysis_worker": "text_analysis_worker",
                "api_interaction_worker": "api_interaction_worker", 
                "data_processing_worker": "data_processing_worker",
                "process_task_result": "process_task_result",
                "__end__": END
            }
        )
        
        # Return edges from workers back to result processing
        graph.add_edge("text_analysis_worker", "process_task_result")
        graph.add_edge("api_interaction_worker", "process_task_result")
        graph.add_edge("data_processing_worker", "process_task_result")
        
        # End after processing results
        graph.add_edge("process_task_result", END)
        
        # Compile the graph
        self.enhanced_graph = graph.compile(checkpointer=self.checkpointer)
        
        logger.info("Enhanced supervisor graph compiled successfully")
    
    def _supervisor_dispatch_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get task from state
            task_data = state.get("task_to_assign")
            if not task_data:
                logger.warning("No task data provided to supervisor")
                state["next_agent"] = None
                return state
            
            # Create Task object
            if isinstance(task_data, dict):
                task = Task(
                    task_id=task_data.get("task_id", str(uuid.uuid4())),
                    title=task_data.get("title", "Untitled Task"),
                    description=task_data.get("description", ""),
                    task_type=task_data.get("task_type", "general"),
                    parameters=task_data.get("parameters", {}),
                    required_capabilities=task_data.get("required_capabilities", []),
                    priority=TaskPriority(task_data.get("priority", "medium"))
                )
            else:
                task = task_data
            
            # Select appropriate worker agent
            selected_agent = self._select_worker_for_task(task)
            
            if selected_agent:
                # Update state with task assignment
                state["current_task"] = {
                    "task_id": task.task_id,
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "parameters": task.parameters,
                    "assigned_agent": selected_agent
                }
                state["next_agent"] = selected_agent
                state["task_status"] = "assigned"
                
                logger.info(f"Task {task.task_id} assigned to {selected_agent} worker")
                
                # Update agent status if we have the agent object
                if selected_agent in self.worker_agents:
                    worker = self.worker_agents[selected_agent]
                    worker.start_task(task)
                
            else:
                # No suitable agent found
                self.task_queue.append(task)
                state["next_agent"] = None
                state["task_status"] = "queued"
                logger.warning(f"No suitable agent for task {task.task_id}, added to queue")
            
            # Update system metrics
            state["system_metrics"] = {
                "total_agents": len(self.worker_agents),
                "available_agents": len([a for a in self.worker_agents.values() 
                                       if a.status == AgentStatus.AVAILABLE]),
                "queued_tasks": len(self.task_queue),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Supervisor dispatch failed: {str(e)}")
            state["error"] = str(e)
            state["next_agent"] = None
            
        return state
    
    def _select_worker_for_task(self, task: Task) -> Optional[str]:
        # Task type to worker mapping
        task_type_mapping = {
            "text_analysis": "text_analysis",
            "summarize": "text_analysis",
            "api_request": "api_interaction", 
            "fetch_data": "api_interaction",
            "http_request": "api_interaction",
            "data_processing": "data_processing",
            "calculate_statistics": "data_processing",
            "analysis": "data_processing"
        }
        
        # First try direct task type mapping
        if task.task_type in task_type_mapping:
            agent_type = task_type_mapping[task.task_type]
            if agent_type in self.worker_agents:
                worker = self.worker_agents[agent_type]
                if worker.status == AgentStatus.AVAILABLE and worker.can_handle_task(task):
                    return agent_type
        
        # Fallback: check all available agents
        for agent_name, worker in self.worker_agents.items():
            if worker.status == AgentStatus.AVAILABLE and worker.can_handle_task(task):
                return agent_name
        
        return None
    
    def _text_analysis_worker_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return self._execute_worker_task(state, "text_analysis")
    
    def _api_interaction_worker_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return self._execute_worker_task(state, "api_interaction")
    
    def _data_processing_worker_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return self._execute_worker_task(state, "data_processing")
    
    def _execute_worker_task(self, state: Dict[str, Any], worker_type: str) -> Dict[str, Any]:
        try:
            current_task = state.get("current_task")
            if not current_task:
                logger.error(f"No current task for {worker_type} worker")
                state["execution_error"] = "No task assigned"
                return state
            
            # Get the worker agent
            worker = self.worker_agents.get(worker_type)
            if not worker:
                logger.error(f"Worker {worker_type} not found")
                state["execution_error"] = f"Worker {worker_type} not available"
                return state
            
            # Create Task object for execution
            task = Task(
                task_id=current_task["task_id"],
                title=current_task["title"],
                description=current_task["description"],
                task_type=current_task["task_type"],
                parameters=current_task["parameters"]
            )
            
            # Execute the task
            start_time = datetime.utcnow()
            result = worker.execute(task, state)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update state with results
            state["task_result"] = result
            state["execution_time"] = execution_time
            state["executed_by"] = worker_type
            state["task_status"] = "completed" if not result.get("error") else "failed"
            
            # Update worker performance
            success = not result.get("error")
            worker.complete_task(task, execution_time, success)
            
            logger.info(f"Task {task.task_id} executed by {worker_type} in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Worker {worker_type} execution failed: {str(e)}")
            state["execution_error"] = str(e)
            state["task_status"] = "failed"
            
            # Mark worker error if we have the worker
            if worker_type in self.worker_agents:
                self.worker_agents[worker_type].set_error(str(e))
        
        return state
    
    def _process_task_result_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            task_result = state.get("task_result")
            current_task = state.get("current_task")
            
            if task_result and current_task:
                # Create final result summary
                state["final_result"] = {
                    "task_id": current_task["task_id"],
                    "task_type": current_task["task_type"],
                    "executed_by": state.get("executed_by"),
                    "execution_time": state.get("execution_time"),
                    "status": state.get("task_status"),
                    "result": task_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Clear current task
                state["current_task"] = None
                state["next_agent"] = None
                
                logger.info(f"Task result processed successfully")
            else:
                logger.warning("No task result to process")
                state["final_result"] = {
                    "status": "no_result",
                    "message": "No task result available"
                }
            
        except Exception as e:
            logger.error(f"Result processing failed: {str(e)}")
            state["final_result"] = {
                "status": "error",
                "error": str(e)
            }
        
        return state
    
    def register_worker_agents(self) -> Dict[str, Any]:
        try:
            # Create worker agent instances
            text_agent = TextAnalysisAgent("MainTextAnalyzer")
            api_agent = APIInteractionAgent("MainAPIClient") 
            data_agent = DataProcessingAgent("MainDataProcessor")
            
            # Store worker agents
            self.worker_agents = {
                "text_analysis": text_agent,
                "api_interaction": api_agent,
                "data_processing": data_agent
            }
            
            # Register with internal registry
            for agent_name, agent in self.worker_agents.items():
                self.agent_registry[agent.agent_id] = agent.get_state()
            
            result = {
                "success": True,
                "registered_agents": len(self.worker_agents),
                "agent_details": {
                    name: {
                        "agent_id": agent.agent_id,
                        "capabilities": [cap.value for cap in agent.capabilities]
                    }
                    for name, agent in self.worker_agents.items()
                }
            }
            
            logger.info(f"Registered {len(self.worker_agents)} worker agents")
            return result
            
        except Exception as e:
            logger.error(f"Worker registration failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def dispatch_task(self, task_data: Dict[str, Any], thread_id: str = "main") -> Dict[str, Any]:
        try:
            initial_state = {
                "task_to_assign": task_data,
                "thread_id": thread_id
            }
            
            config = {"configurable": {"thread_id": thread_id}}
            result = self.enhanced_graph.invoke(initial_state, config)
            
            return result.get("final_result", {"status": "unknown", "error": "No result"})
            
        except Exception as e:
            logger.error(f"Task dispatch failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "supervisor_active": True,
            "registered_agents": len(self.worker_agents),
            "available_agents": len([a for a in self.worker_agents.values() 
                                   if a.status == AgentStatus.AVAILABLE]),
            "queued_tasks": len(self.task_queue),
            "worker_details": {
                name: {
                    "status": agent.status.value,
                    "tasks_completed": agent.agent_state.tasks_completed,
                    "success_rate": agent.agent_state.success_rate
                }
                for name, agent in self.worker_agents.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
