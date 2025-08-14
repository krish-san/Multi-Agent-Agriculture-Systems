
from typing import Dict, Any, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator
from datetime import datetime
import json

from .models import (
    SystemState, AgentState, WorkflowState, Task, Message,
    AgentStatus, TaskStatus, MessageType
)


class GraphState(TypedDict):
    # Core system state
    system_state: SystemState
    
    # Current execution context
    current_agent_id: Optional[str]
    current_task_id: Optional[str]
    current_workflow_id: Optional[str]
    
    # Message queue and communication
    message_queue: Annotated[list[Message], operator.add]
    
    # Execution metadata
    execution_log: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
    
    # Shared context for agents
    shared_context: Dict[str, Any]


class StateManager:
    
    def __init__(self):
        self.memory_saver = MemorySaver()
        self.thread_id = "agentweaver-main"
        
        # Initialize empty system state
        self.system_state = SystemState()
        
        # Create the graph for state management
        self.graph = self._create_state_graph()
    
    def _create_state_graph(self) -> StateGraph:
        
        def state_update_node(state: GraphState) -> GraphState:
            # Update system metrics
            state["system_state"].update_metrics()
            
            # Log the state update
            timestamp = datetime.utcnow().isoformat()
            state["execution_log"].append(f"{timestamp}: State updated")
            
            return state
        
        def message_processor_node(state: GraphState) -> GraphState:
            processed_messages = []
            
            for message in state["message_queue"]:
                if not message.processed:
                    # Mark message as processed
                    message.processed = True
                    processed_messages.append(message.message_id)
                    
                    # Log message processing
                    timestamp = datetime.utcnow().isoformat()
                    state["execution_log"].append(
                        f"{timestamp}: Processed message {message.message_id} "
                        f"from {message.sender_id} to {message.receiver_id}"
                    )
            
            return state
        
        # Create the workflow
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("state_update", state_update_node)
        workflow.add_node("message_processor", message_processor_node)
        
        # Set entry point
        workflow.set_entry_point("state_update")
        
        # Add edges
        workflow.add_edge("state_update", "message_processor")
        workflow.add_edge("message_processor", END)
        
        # Compile with memory
        return workflow.compile(checkpointer=self.memory_saver)
    
    def get_current_state(self) -> GraphState:
        try:
            # Try to get existing state
            config = {"configurable": {"thread_id": self.thread_id}}
            state = self.graph.get_state(config)
            
            if state and state.values:
                return state.values
            else:
                # Return initial state
                return self._get_initial_state()
        except Exception:
            # Return initial state if retrieval fails
            return self._get_initial_state()
    
    def _get_initial_state(self) -> GraphState:
        return {
            "system_state": self.system_state,
            "current_agent_id": None,
            "current_task_id": None,
            "current_workflow_id": None,
            "message_queue": [],
            "execution_log": [],
            "errors": [],
            "shared_context": {}
        }
    
    def update_state(self, updates: Dict[str, Any]) -> GraphState:
        current_state = self.get_current_state()
        
        # Apply updates
        for key, value in updates.items():
            if key in current_state:
                current_state[key] = value
        
        # Execute the state update through the graph
        config = {"configurable": {"thread_id": self.thread_id}}
        result = self.graph.invoke(current_state, config)
        
        return result
    
    # Agent management methods
    
    def register_agent(self, agent: AgentState) -> bool:
        try:
            current_state = self.get_current_state()
            current_state["system_state"].agents[agent.agent_id] = agent
            
            # Update state
            self.update_state({"system_state": current_state["system_state"]})
            
            return True
        except Exception as e:
            self._log_error(f"Failed to register agent {agent.agent_id}: {str(e)}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        current_state = self.get_current_state()
        return current_state["system_state"].agents.get(agent_id)
    
    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        try:
            current_state = self.get_current_state()
            if agent_id in current_state["system_state"].agents:
                current_state["system_state"].agents[agent_id].status = status
                current_state["system_state"].agents[agent_id].last_activity = datetime.utcnow()
                
                self.update_state({"system_state": current_state["system_state"]})
                return True
            return False
        except Exception as e:
            self._log_error(f"Failed to update agent status: {str(e)}")
            return False
    
    def get_available_agents(self) -> list[AgentState]:
        current_state = self.get_current_state()
        return [
            agent for agent in current_state["system_state"].agents.values()
            if agent.status == AgentStatus.IDLE
        ]
    
    # Task management methods
    
    def create_task(self, task: Task) -> bool:
        try:
            current_state = self.get_current_state()
            current_state["system_state"].tasks[task.task_id] = task
            
            self.update_state({"system_state": current_state["system_state"]})
            return True
        except Exception as e:
            self._log_error(f"Failed to create task {task.task_id}: {str(e)}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        current_state = self.get_current_state()
        return current_state["system_state"].tasks.get(task_id)
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        try:
            current_state = self.get_current_state()
            
            # Check if task and agent exist
            if (task_id not in current_state["system_state"].tasks or 
                agent_id not in current_state["system_state"].agents):
                return False
            
            # Update task and agent
            task = current_state["system_state"].tasks[task_id]
            agent = current_state["system_state"].agents[agent_id]
            
            task.start_task(agent_id)
            agent.current_task_id = task_id
            agent.status = AgentStatus.BUSY
            
            self.update_state({"system_state": current_state["system_state"]})
            return True
        except Exception as e:
            self._log_error(f"Failed to assign task {task_id} to agent {agent_id}: {str(e)}")
            return False
    
    def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        try:
            current_state = self.get_current_state()
            
            if task_id not in current_state["system_state"].tasks:
                return False
            
            task = current_state["system_state"].tasks[task_id]
            task.complete_task(result)
            
            # Free up the agent
            if task.assigned_agent_id:
                agent = current_state["system_state"].agents.get(task.assigned_agent_id)
                if agent:
                    agent.current_task_id = None
                    agent.status = AgentStatus.AVAILABLE
                    
                    # Update performance metrics
                    execution_time = (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
                    agent.update_performance(execution_time, True)
            
            self.update_state({"system_state": current_state["system_state"]})
            return True
        except Exception as e:
            self._log_error(f"Failed to complete task {task_id}: {str(e)}")
            return False
    
    # Message management methods
    
    def send_message(self, message: Message) -> bool:
        try:
            current_state = self.get_current_state()
            
            # Add message to system messages
            current_state["system_state"].messages[message.message_id] = message
            
            # Also add to message queue for processing
            if "message_queue" not in current_state:
                current_state["message_queue"] = []
            current_state["message_queue"].append(message)
            
            # Update the state
            self.update_state(current_state)
            return True
        except Exception as e:
            self._log_error(f"Failed to send message {message.message_id}: {str(e)}")
            return False
    
    def get_messages_for_agent(self, agent_id: str) -> list[Message]:
        current_state = self.get_current_state()
        # Check both system messages and message queue
        system_messages = [
            msg for msg in current_state["system_state"].messages.values()
            if msg.receiver_id == agent_id and not msg.processed
        ]
        queue_messages = [
            msg for msg in current_state.get("message_queue", [])
            if msg.receiver_id == agent_id and not msg.processed
        ]
        
        # Combine and deduplicate by message_id
        all_messages = {}
        for msg in system_messages + queue_messages:
            all_messages[msg.message_id] = msg
        
        return list(all_messages.values())
    
    # Workflow management methods
    
    def create_workflow(self, workflow: WorkflowState) -> bool:
        try:
            current_state = self.get_current_state()
            current_state["system_state"].workflows[workflow.workflow_id] = workflow
            
            self.update_state({"system_state": current_state["system_state"]})
            return True
        except Exception as e:
            self._log_error(f"Failed to create workflow {workflow.workflow_id}: {str(e)}")
            return False
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        current_state = self.get_current_state()
        return current_state["system_state"].workflows.get(workflow_id)
    
    # Utility methods
    
    def get_system_metrics(self) -> Dict[str, Any]:
        current_state = self.get_current_state()
        system_state = current_state["system_state"]
        system_state.update_metrics()
        
        return {
            "total_agents": system_state.total_agents,
            "active_agents": system_state.active_agents,
            "total_workflows": system_state.total_workflows,
            "active_workflows": system_state.active_workflows,
            "total_tasks": system_state.total_tasks,
            "completed_tasks": system_state.completed_tasks,
            "pending_messages": len([m for m in system_state.messages.values() if not m.processed]),
            "last_updated": system_state.last_updated.isoformat()
        }
    
    def export_state(self) -> Dict[str, Any]:
        current_state = self.get_current_state()
        return {
            "system_state": current_state["system_state"].model_dump(),
            "execution_log": current_state["execution_log"][-50:],  # Last 50 entries
            "errors": current_state["errors"][-20:],  # Last 20 errors
            "metrics": self.get_system_metrics()
        }
    
    def _log_error(self, error_message: str) -> None:
        try:
            current_state = self.get_current_state()
            timestamp = datetime.utcnow().isoformat()
            current_state["errors"].append(f"{timestamp}: {error_message}")
            
            # Keep only the last 100 errors
            if len(current_state["errors"]) > 100:
                current_state["errors"] = current_state["errors"][-100:]
            
            self.update_state({"errors": current_state["errors"]})
        except Exception:
            # If we can't log the error, at least print it
            print(f"ERROR: {error_message}")
    
    def reset_state(self) -> None:
        initial_state = self._get_initial_state()
        config = {"configurable": {"thread_id": self.thread_id}}
        self.graph.invoke(initial_state, config)
