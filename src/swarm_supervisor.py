
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import uuid
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import copy

from .supervisor import SupervisorNode
from .models import (
    AgentState, Task, Message, WorkflowState, SystemState,
    TaskStatus, TaskPriority, MessageType, MessagePriority, 
    AgentCapability, AgentStatus
)
from .parallel_execution_nodes import (
    ParallelForkNode, ParallelWorkerNode, ParallelAggregatorNode,
    create_parallel_execution_router
)

logger = logging.getLogger(__name__)


class SwarmSupervisorNode(SupervisorNode):
    
    def __init__(self, checkpointer=None, max_parallel_workers: int = 4):
        super().__init__(checkpointer)
        self.max_parallel_workers = max_parallel_workers
        self.parallel_task_registry: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_parallel_workers)
        
        # Initialize parallel execution nodes
        self.fork_node = ParallelForkNode(max_concurrent_tasks=max_parallel_workers)
        self.worker_node = ParallelWorkerNode(agent_registry=self.agent_registry)
        self.aggregator_node = ParallelAggregatorNode()
        
        # Override the graph setup to include parallel processing nodes
        self._setup_swarm_supervisor_graph()
    
    def _setup_swarm_supervisor_graph(self):
        from langgraph.graph import StateGraph, START, END
        
        # Create the graph with our SystemState
        graph = StateGraph(dict)
        
        # Add existing supervisor nodes
        graph.add_node("register_agent", self._register_agent_node)
        graph.add_node("unregister_agent", self._unregister_agent_node)
        graph.add_node("assign_task", self._enhanced_assign_task_node)
        graph.add_node("monitor_health", self._monitor_health_node)
        graph.add_node("process_supervisor_message", self._process_supervisor_message_node)
        
        # Add new parallel processing nodes using the dedicated classes
        graph.add_node("detect_parallelizable_task", self._detect_parallelizable_task_node)
        graph.add_node("split_parallel_task", self._split_parallel_task_node)
        graph.add_node("fork", self.fork_node)
        graph.add_node("worker", self.worker_node)
        graph.add_node("aggregator", self.aggregator_node)
        
        # Enhanced routing function with parallel processing support
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
                # Check if task can be parallelized
                task_data = state.get("task_to_assign")
                if self._is_parallelizable_task(task_data):
                    return "detect_parallelizable_task"
                else:
                    return "assign_task"
            elif message_type == "health_check":
                return "monitor_health"
            else:
                return "monitor_health"  # Default
        
        # Define conditional routing for parallel processing
        def route_after_detection(state: Dict[str, Any]) -> str:
            if state.get("is_parallelizable", False):
                return "split_parallel_task"
            else:
                return "assign_task"
        
        def route_after_split(state: Dict[str, Any]) -> str:
            return "fork"
        
        # Add edges with conditional routing
        graph.add_edge(START, "process_supervisor_message")
        graph.add_conditional_edges(
            "process_supervisor_message",
            route_message,
            {
                "register_agent": "register_agent",
                "unregister_agent": "unregister_agent", 
                "assign_task": "assign_task",
                "detect_parallelizable_task": "detect_parallelizable_task",
                "monitor_health": "monitor_health"
            }
        )
        
        # Parallel processing flow
        graph.add_conditional_edges(
            "detect_parallelizable_task",
            route_after_detection,
            {
                "split_parallel_task": "split_parallel_task",
                "assign_task": "assign_task"
            }
        )
        
        graph.add_conditional_edges(
            "split_parallel_task",
            route_after_split,
            {"fork": "fork"}
        )
        
        # Use the router from parallel_execution_nodes
        graph.add_conditional_edges(
            "fork",
            create_parallel_execution_router,
            {
                "worker": "worker",
                "aggregator": "aggregator"
            }
        )
        
        graph.add_conditional_edges(
            "worker", 
            create_parallel_execution_router,
            {
                "worker": "worker",
                "aggregator": "aggregator"
            }
        )
        
        # Regular task assignment and health monitoring end states
        graph.add_edge("assign_task", END)
        graph.add_edge("aggregator", END)
        graph.add_edge("register_agent", END)
        graph.add_edge("unregister_agent", END)
        graph.add_edge("monitor_health", END)
        
        # Compile the graph
        self.graph = graph.compile(checkpointer=self.checkpointer)
    
    def _is_parallelizable_task(self, task_data: Optional[Dict[str, Any]]) -> bool:
        if not task_data:
            return False
        
        # Check for explicit parallelizable flag
        if task_data.get("parallelizable", False):
            return True
        
        # Check for list-based data in parameters
        parameters = task_data.get("parameters", {})
        
        # Look for list data structures that can be processed in parallel
        for key, value in parameters.items():
            if isinstance(value, list) and len(value) > 1:
                # Check if the list contains processable items
                if key in ["items", "data_list", "texts", "documents", "files", "urls"]:
                    return True
                if len(value) >= 3:  # Arbitrary threshold for parallel processing
                    return True
        
        # Check for specific task types that are inherently parallelizable
        task_type = task_data.get("task_type", "")
        parallelizable_types = [
            "batch_processing", 
            "data_analysis", 
            "text_processing",
            "sentiment_analysis",
            "document_processing",
            "web_scraping",
            "image_processing"
        ]
        
        if task_type in parallelizable_types:
            return True
        
        # Check if description suggests parallel processing
        description = task_data.get("description", "").lower()
        parallel_keywords = ["batch", "multiple", "list of", "process all", "analyze each"]
        
        if any(keyword in description for keyword in parallel_keywords):
            return True
        
        return False
    
    def _detect_parallelizable_task_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            task_data = state.get("task_to_assign")
            if not task_data:
                state["is_parallelizable"] = False
                return state
            
            is_parallelizable = self._is_parallelizable_task(task_data)
            state["is_parallelizable"] = is_parallelizable
            
            if is_parallelizable:
                logger.info(f"Task {task_data.get('task_id', 'unknown')} detected as parallelizable")
                state["parallel_detection_result"] = {
                    "success": True,
                    "parallelizable": True,
                    "message": "Task can be processed in parallel"
                }
            else:
                logger.info(f"Task {task_data.get('task_id', 'unknown')} will be processed sequentially")
                state["parallel_detection_result"] = {
                    "success": True,
                    "parallelizable": False,
                    "message": "Task will be processed sequentially"
                }
            
        except Exception as e:
            logger.error(f"Failed to detect parallelizable task: {str(e)}")
            state["is_parallelizable"] = False
            state["parallel_detection_result"] = {
                "success": False,
                "error": str(e)
            }
        
        return state
    
    def _split_parallel_task_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            task_data = state.get("task_to_assign")
            if not task_data:
                logger.error("No task data provided for splitting")
                return state
            
            # Extract the original task information
            original_task_id = task_data.get("task_id", str(uuid.uuid4()))
            base_title = task_data.get("title", "Parallel Task")
            base_description = task_data.get("description", "")
            parameters = task_data.get("parameters", {})
            required_capabilities = task_data.get("required_capabilities", [])
            priority = task_data.get("priority", "medium")
            
            # Find the data to split
            sub_tasks = []
            data_to_process = None
            data_key = None
            
            # Look for list data in parameters
            for key, value in parameters.items():
                if isinstance(value, list) and len(value) > 1:
                    if key in ["items", "data_list", "texts", "documents", "files", "urls"] or len(value) >= 3:
                        data_to_process = value
                        data_key = key
                        break
            
            if data_to_process:
                # Split the data into sub-tasks
                for i, item in enumerate(data_to_process):
                    sub_task = {
                        "task_id": f"{original_task_id}_subtask_{i}",
                        "title": f"{base_title} - Part {i+1}",
                        "description": f"{base_description} (Processing item {i+1} of {len(data_to_process)})",
                        "task_type": task_data.get("task_type", "general"),
                        "required_capabilities": required_capabilities,
                        "priority": priority,
                        "parameters": {
                            **{k: v for k, v in parameters.items() if k != data_key},
                            "item": item,
                            "item_index": i,
                            "total_items": len(data_to_process),
                            "original_task_id": original_task_id,
                            "is_subtask": True
                        }
                    }
                    sub_tasks.append(sub_task)
            else:
                # If no obvious list data, try to split based on task type or other criteria
                # For now, create a simple split
                num_parts = min(self.max_parallel_workers, 4)  # Default to 4 parts
                for i in range(num_parts):
                    sub_task = {
                        "task_id": f"{original_task_id}_subtask_{i}",
                        "title": f"{base_title} - Part {i+1}",
                        "description": f"{base_description} (Part {i+1} of {num_parts})",
                        "task_type": task_data.get("task_type", "general"),
                        "required_capabilities": required_capabilities,
                        "priority": priority,
                        "parameters": {
                            **parameters,
                            "part_index": i,
                            "total_parts": num_parts,
                            "original_task_id": original_task_id,
                            "is_subtask": True
                        }
                    }
                    sub_tasks.append(sub_task)
            
            # Store sub-tasks in state
            state["sub_tasks_to_process"] = sub_tasks
            state["processed_results"] = []
            state["original_task_data"] = task_data
            state["parallel_task_id"] = original_task_id
            
            # Register the parallel task
            self.parallel_task_registry[original_task_id] = {
                "original_task": task_data,
                "sub_tasks": sub_tasks,
                "started_at": datetime.utcnow(),
                "status": "running",
                "results": []
            }
            
            logger.info(f"Split task {original_task_id} into {len(sub_tasks)} sub-tasks")
            state["split_result"] = {
                "success": True,
                "original_task_id": original_task_id,
                "sub_task_count": len(sub_tasks),
                "message": f"Task split into {len(sub_tasks)} parallel sub-tasks"
            }
            
        except Exception as e:
            logger.error(f"Failed to split parallel task: {str(e)}")
            state["split_result"] = {
                "success": False,
                "error": str(e)
            }
        
        return state
    
    def _enhanced_assign_task_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Check if this is part of a parallel execution
        is_subtask = False
        if "task_to_assign" in state:
            task_data = state["task_to_assign"]
            is_subtask = task_data.get("parameters", {}).get("is_subtask", False)
        
        if is_subtask:
            logger.info("Processing sub-task assignment within parallel execution")
        
        # Call the original assignment logic
        result_state = super()._assign_task_node(state)
        
        # Add parallel processing context if needed
        if is_subtask and "assignment_result" in result_state:
            assignment_result = result_state["assignment_result"]
            if assignment_result.get("success"):
                original_task_id = task_data.get("parameters", {}).get("original_task_id")
                if original_task_id and original_task_id in self.parallel_task_registry:
                    self.parallel_task_registry[original_task_id]["sub_tasks_assigned"] = \
                        self.parallel_task_registry[original_task_id].get("sub_tasks_assigned", 0) + 1
        
        return result_state
    
    def execute_parallel_task(self, task_data: Dict[str, Any], thread_id: str = "swarm_supervisor") -> Dict[str, Any]:
        try:
            # Prepare state for execution
            initial_state = {
                "message": {
                    "type": "assign_task",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "task_to_assign": task_data
            }
            
            # Execute the enhanced supervisor graph
            result = self.graph.invoke(initial_state, {"configurable": {"thread_id": thread_id}})
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute parallel task: {str(e)}")
            return {
                "error": str(e),
                "task_id": task_data.get("task_id", "unknown")
            }
    
    def get_parallel_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.parallel_task_registry.get(task_id)
    
    def list_parallel_tasks(self) -> List[Dict[str, Any]]:
        return list(self.parallel_task_registry.values())
    
    def cleanup_completed_parallel_tasks(self, max_age_hours: int = 24):
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        tasks_to_remove = []
        for task_id, task_info in self.parallel_task_registry.items():
            if (task_info.get("status") == "completed" and 
                task_info.get("completed_at") and 
                task_info["completed_at"] < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.parallel_task_registry[task_id]
            logger.info(f"Cleaned up completed parallel task {task_id}")
        
        return len(tasks_to_remove)
