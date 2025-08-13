
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import logging
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..core.models import Task, TaskStatus
from ..agents import TextAnalysisAgent, APIInteractionAgent, DataProcessingAgent
from .p2p_communication import (
    AgentMessage, MessageType, MessagePriority, 
    CollaborationProtocol, get_p2p_manager
)
from ..core.redis_config import get_redis_saver

logger = logging.getLogger(__name__)


class TeamRole(Enum):
    SUPERVISOR = "supervisor"
    TEAM_LEAD = "team_lead"
    SPECIALIST = "specialist"
    COORDINATOR = "coordinator"
    WORKER = "worker"


class TeamStructure(BaseModel):
    
    team_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_name: str
    
    # Team hierarchy
    supervisor_id: Optional[str] = None
    team_leads: List[str] = Field(default_factory=list)
    members: Dict[str, str] = Field(default_factory=dict)  # agent_id -> role
    
    # Team capabilities
    team_capabilities: List[str] = Field(default_factory=list)
    specializations: Dict[str, List[str]] = Field(default_factory=dict)  # agent_id -> capabilities
    
    # Management metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active_tasks: List[str] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    
    def add_member(self, agent_id: str, role: TeamRole, capabilities: List[str] = None):
        self.members[agent_id] = role.value
        if capabilities:
            self.specializations[agent_id] = capabilities
            # Add to team capabilities if not already present
            for cap in capabilities:
                if cap not in self.team_capabilities:
                    self.team_capabilities.append(cap)
    
    def get_members_by_role(self, role: TeamRole) -> List[str]:
        return [agent_id for agent_id, agent_role in self.members.items() 
                if agent_role == role.value]
    
    def get_available_capabilities(self) -> List[str]:
        return self.team_capabilities.copy()
    
    def find_agents_with_capability(self, capability: str) -> List[str]:
        return [agent_id for agent_id, caps in self.specializations.items() 
                if capability in caps]


class TaskDelegation(BaseModel):
    
    delegation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: Optional[str] = None
    
    # Delegation details
    supervisor_id: str
    delegated_to: str
    task_description: str
    task_parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing and constraints
    delegated_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    estimated_duration: Optional[float] = None  # seconds
    
    # Status tracking
    status: str = "assigned"  # assigned, in_progress, completed, failed, cancelled
    progress_reports: List[Dict[str, Any]] = Field(default_factory=list)
    result_data: Optional[Dict[str, Any]] = None
    
    # Communication tracking
    message_thread: List[str] = Field(default_factory=list)  # message IDs
    last_update: datetime = Field(default_factory=datetime.utcnow)
    
    def add_progress_report(self, report_data: Dict[str, Any]):
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "data": report_data
        }
        self.progress_reports.append(report)
        self.last_update = datetime.utcnow()
    
    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline


class HierarchicalWorkflowState(BaseModel):
    
    # Workflow identification
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str = "Hierarchical Team Workflow"
    
    # Hierarchical structure
    team_structure: Optional[TeamStructure] = None
    active_delegations: Dict[str, TaskDelegation] = Field(default_factory=dict)
    
    # Task coordination
    main_task: Optional[Dict[str, Any]] = None
    sub_tasks: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    task_assignments: Dict[str, str] = Field(default_factory=dict)  # task_id -> agent_id
    
    # Communication state
    pending_messages: List[AgentMessage] = Field(default_factory=list)
    coordination_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Results aggregation
    partial_results: Dict[str, Any] = Field(default_factory=dict)
    consolidated_result: Optional[Dict[str, Any]] = None
    
    # Execution tracking
    workflow_start_time: datetime = Field(default_factory=datetime.utcnow)
    workflow_end_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    
    # Status tracking
    status: str = "initializing"  # initializing, coordinating, executing, consolidating, completed, failed
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TeamLeadAgent:
    
    def __init__(self, agent_id: str, team_structure: TeamStructure):
        self.agent_id = agent_id
        self.team_structure = team_structure
        self.active_delegations: Dict[str, TaskDelegation] = {}
        self.p2p_manager = get_p2p_manager()
        
        # Register with P2P communication
        self.p2p_manager.register_agent(agent_id)
        
        logger.info(f"Team Lead Agent {agent_id} initialized for team {team_structure.team_name}")
    
    def delegate_task(self, task_description: str, task_parameters: Dict[str, Any],
                     required_capability: str, deadline: Optional[datetime] = None) -> Optional[TaskDelegation]:
        # Find suitable team members
        suitable_agents = self.team_structure.find_agents_with_capability(required_capability)
        
        if not suitable_agents:
            logger.error(f"No agents with capability '{required_capability}' available for delegation")
            return None
        
        # Select the first available agent (could be enhanced with load balancing)
        selected_agent = suitable_agents[0]
        
        # Create delegation
        delegation = TaskDelegation(
            supervisor_id=self.agent_id,
            delegated_to=selected_agent,
            task_description=task_description,
            task_parameters=task_parameters,
            deadline=deadline
        )
        
        # Create delegation message
        delegation_message = CollaborationProtocol.create_delegation_message(
            supervisor_id=self.agent_id,
            subordinate_id=selected_agent,
            task_title=task_description,
            task_parameters=task_parameters,
            deadline=deadline
        )
        
        # Send delegation message
        if self.p2p_manager.send_message(delegation_message):
            self.active_delegations[delegation.delegation_id] = delegation
            delegation.message_thread.append(delegation_message.message_id)
            
            logger.info(f"Task delegated to {selected_agent}: {task_description}")
            return delegation
        else:
            logger.error(f"Failed to send delegation message to {selected_agent}")
            return None
    
    def process_incoming_messages(self) -> List[Dict[str, Any]]:
        messages = self.p2p_manager.get_messages_for_agent(self.agent_id)
        processed_summaries = []
        
        for message in messages:
            summary = self._process_message(message)
            if summary:
                processed_summaries.append(summary)
            
            # Mark message as processed
            self.p2p_manager.mark_message_processed(self.agent_id, message.message_id)
        
        return processed_summaries
    
    def _process_message(self, message: AgentMessage) -> Optional[Dict[str, Any]]:
        try:
            if message.message_type == MessageType.REPORT:
                return self._handle_status_report(message)
            elif message.message_type == MessageType.RESPONSE:
                return self._handle_task_response(message)
            elif message.message_type == MessageType.REQUEST:
                return self._handle_request(message)
            else:
                logger.info(f"Received {message.message_type.value} message from {message.sender_id}")
                return {
                    "type": "message_received",
                    "from": message.sender_id,
                    "message_type": message.message_type.value,
                    "subject": message.subject
                }
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {str(e)}")
            return None
    
    def _handle_status_report(self, message: AgentMessage) -> Dict[str, Any]:
        content = message.content
        task_id = content.get("task_id")
        status = content.get("status")
        progress_data = content.get("progress_data", {})
        
        # Find the relevant delegation
        delegation = None
        for d in self.active_delegations.values():
            if d.delegated_to == message.sender_id and task_id in str(d.delegation_id):
                delegation = d
                break
        
        if delegation:
            delegation.add_progress_report(progress_data)
            delegation.status = status
            
            if status == "completed":
                delegation.result_data = progress_data
            
            logger.info(f"Status update from {message.sender_id}: {status}")
        
        return {
            "type": "status_report",
            "from": message.sender_id,
            "task_id": task_id,
            "status": status,
            "delegation_found": delegation is not None
        }
    
    def _handle_task_response(self, message: AgentMessage) -> Dict[str, Any]:
        content = message.content
        
        # Update delegation status
        for delegation in self.active_delegations.values():
            if delegation.delegated_to == message.sender_id:
                delegation.status = "completed"
                delegation.result_data = content
                break
        
        return {
            "type": "task_response",
            "from": message.sender_id,
            "result": content
        }
    
    def _handle_request(self, message: AgentMessage) -> Dict[str, Any]:
        # Could handle requests for resources, clarification, etc.
        return {
            "type": "request",
            "from": message.sender_id,
            "subject": message.subject,
            "content": message.content
        }
    
    def get_team_status(self) -> Dict[str, Any]:
        active_count = len([d for d in self.active_delegations.values() if d.status in ["assigned", "in_progress"]])
        completed_count = len([d for d in self.active_delegations.values() if d.status == "completed"])
        overdue_count = len([d for d in self.active_delegations.values() if d.is_overdue()])
        
        return {
            "team_id": self.team_structure.team_id,
            "team_name": self.team_structure.team_name,
            "team_size": len(self.team_structure.members),
            "active_delegations": active_count,
            "completed_delegations": completed_count,
            "overdue_delegations": overdue_count,
            "team_capabilities": self.team_structure.team_capabilities,
            "delegations": [
                {
                    "id": d.delegation_id,
                    "to": d.delegated_to,
                    "description": d.task_description,
                    "status": d.status,
                    "overdue": d.is_overdue()
                }
                for d in self.active_delegations.values()
            ]
        }


class HierarchicalWorkflowOrchestrator:
    
    def __init__(self, use_redis: bool = True):
        # Initialize persistent state management
        if use_redis:
            try:
                self.checkpointer = get_redis_saver()
                logger.info("Using Redis for hierarchical workflow persistence")
            except Exception as e:
                logger.error(f"Failed to initialize Redis, using memory fallback: {str(e)}")
                self.checkpointer = MemorySaver()
        else:
            self.checkpointer = MemorySaver()
        
        # Initialize team structure and agents
        self.teams: Dict[str, TeamStructure] = {}
        self.team_leads: Dict[str, TeamLeadAgent] = {}
        self.worker_agents = self._initialize_worker_agents()
        self.p2p_manager = get_p2p_manager()
        
        # Build default team structure
        self._setup_default_teams()
        
        logger.info("Hierarchical Workflow Orchestrator initialized")
    
    def _initialize_worker_agents(self) -> Dict[str, Any]:
        return {
            # Analysis Team
            "senior_text_analyst": TextAnalysisAgent("SeniorTextAnalyst"),
            "junior_text_analyst": TextAnalysisAgent("JuniorTextAnalyst"),
            
            # Integration Team  
            "senior_api_specialist": APIInteractionAgent("SeniorAPISpecialist"),
            "junior_api_specialist": APIInteractionAgent("JuniorAPISpecialist"),
            
            # Processing Team
            "senior_data_processor": DataProcessingAgent("SeniorDataProcessor"),
            "junior_data_processor": DataProcessingAgent("JuniorDataProcessor"),
            
            # Coordination
            "workflow_coordinator": DataProcessingAgent("WorkflowCoordinator")
        }
    
    def _setup_default_teams(self):
        # Analysis Team
        analysis_team = TeamStructure(
            team_name="Analysis Team",
            supervisor_id="analysis_supervisor"
        )
        analysis_team.add_member("senior_text_analyst", TeamRole.SPECIALIST, ["text_analysis", "advanced_nlp"])
        analysis_team.add_member("junior_text_analyst", TeamRole.WORKER, ["text_analysis"])
        
        # Integration Team
        integration_team = TeamStructure(
            team_name="Integration Team",
            supervisor_id="integration_supervisor"
        )
        integration_team.add_member("senior_api_specialist", TeamRole.SPECIALIST, ["api_interaction", "system_integration"])
        integration_team.add_member("junior_api_specialist", TeamRole.WORKER, ["api_interaction"])
        
        # Processing Team
        processing_team = TeamStructure(
            team_name="Processing Team", 
            supervisor_id="processing_supervisor"
        )
        processing_team.add_member("senior_data_processor", TeamRole.SPECIALIST, ["data_processing", "advanced_analytics"])
        processing_team.add_member("junior_data_processor", TeamRole.WORKER, ["data_processing"])
        
        # Store teams and create team leads
        self.teams["analysis"] = analysis_team
        self.teams["integration"] = integration_team
        self.teams["processing"] = processing_team
        
        # Create team lead agents
        self.team_leads["analysis_supervisor"] = TeamLeadAgent("analysis_supervisor", analysis_team)
        self.team_leads["integration_supervisor"] = TeamLeadAgent("integration_supervisor", integration_team)
        self.team_leads["processing_supervisor"] = TeamLeadAgent("processing_supervisor", processing_team)
        
        logger.info(f"Created {len(self.teams)} teams with {len(self.team_leads)} team leads")
    
    def create_hierarchical_workflow(self, main_task: Dict[str, Any]) -> StateGraph:
        # Create the graph
        graph = StateGraph(dict)
        
        # Add nodes
        graph.add_node("workflow_coordinator", self._coordinator_node)
        graph.add_node("task_analyzer", self._task_analyzer_node)
        graph.add_node("team_assignment", self._team_assignment_node)
        graph.add_node("parallel_execution", self._parallel_execution_node)
        graph.add_node("progress_monitor", self._progress_monitor_node)
        graph.add_node("result_consolidator", self._result_consolidator_node)
        graph.add_node("workflow_finalizer", self._workflow_finalizer_node)
        
        # Define workflow edges
        graph.add_edge(START, "workflow_coordinator")
        graph.add_edge("workflow_coordinator", "task_analyzer")
        graph.add_edge("task_analyzer", "team_assignment")
        graph.add_edge("team_assignment", "parallel_execution")
        graph.add_edge("parallel_execution", "progress_monitor")
        
        # Conditional routing based on completion status
        def route_from_monitor(state: Dict[str, Any]) -> str:
            if state.get("all_tasks_completed", False):
                return "result_consolidator"
            else:
                return "parallel_execution"  # Continue monitoring
        
        graph.add_conditional_edges(
            "progress_monitor",
            route_from_monitor,
            {
                "result_consolidator": "result_consolidator",
                "parallel_execution": "parallel_execution"
            }
        )
        
        graph.add_edge("result_consolidator", "workflow_finalizer")
        graph.add_edge("workflow_finalizer", END)
        
        # Compile the graph
        compiled_graph = graph.compile(checkpointer=self.checkpointer)
        logger.info("Hierarchical workflow graph compiled successfully")
        
        return compiled_graph
    
    def execute_hierarchical_workflow(self, main_task: Dict[str, Any], 
                                    thread_id: str = "hierarchical_workflow") -> Dict[str, Any]:
        try:
            # Create workflow graph
            workflow_graph = self.create_hierarchical_workflow(main_task)
            
            # Initial state
            initial_state = {
                "main_task": main_task,
                "workflow_id": str(uuid.uuid4()),
                "workflow_name": "Hierarchical Team Workflow",
                "teams": {team_id: team.dict() for team_id, team in self.teams.items()},
                "status": "initializing"
            }
            
            # Execute workflow
            config = {"configurable": {"thread_id": thread_id}}
            final_state = workflow_graph.invoke(initial_state, config)
            
            return final_state
            
        except Exception as e:
            logger.error(f"Hierarchical workflow execution failed: {str(e)}")
            return {
                "status": "critical_failure",
                "error_message": f"Hierarchical workflow execution failed: {str(e)}",
                "consolidated_result": None
            }
    
    # Node implementations will be added in the next part
    def _coordinator_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Hierarchical Workflow: Coordinator initializing")
        
        state["status"] = "coordinating"
        state["workflow_start_time"] = datetime.utcnow().isoformat()
        state["coordination_log"] = []
        
        # Log coordination start
        coordination_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "workflow_coordination_started",
            "details": {
                "main_task": state.get("main_task", {}),
                "available_teams": list(self.teams.keys())
            }
        }
        state["coordination_log"].append(coordination_entry)
        
        logger.info("Hierarchical Workflow: Coordination initialized successfully")
        return state
    
    def _task_analyzer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Hierarchical Workflow: Analyzing main task")
        
        main_task = state.get("main_task", {})
        
        # Simple task breakdown based on task requirements
        sub_tasks = {}
        
        # Example breakdown - would be more sophisticated in practice
        if main_task.get("requires_text_analysis"):
            sub_tasks["text_analysis"] = {
                "team": "analysis",
                "task_type": "text_analysis",
                "parameters": main_task.get("text_data", {}),
                "priority": "high"
            }
        
        if main_task.get("requires_data_processing"):
            sub_tasks["data_processing"] = {
                "team": "processing", 
                "task_type": "data_processing",
                "parameters": main_task.get("processing_data", {}),
                "priority": "normal"
            }
        
        if main_task.get("requires_api_integration"):
            sub_tasks["api_integration"] = {
                "team": "integration",
                "task_type": "api_interaction",
                "parameters": main_task.get("api_data", {}),
                "priority": "normal"
            }
        
        state["sub_tasks"] = sub_tasks
        state["status"] = "analyzed"
        
        logger.info(f"Hierarchical Workflow: Created {len(sub_tasks)} sub-tasks")
        return state
    
    def _team_assignment_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Hierarchical Workflow: Assigning tasks to teams")
        
        sub_tasks = state.get("sub_tasks", {})
        task_assignments = {}
        
        for task_id, task_info in sub_tasks.items():
            team_name = task_info.get("team")
            if team_name in self.team_leads:
                team_lead_id = f"{team_name}_supervisor"
                task_assignments[task_id] = team_lead_id
                
                # Send delegation to team lead
                if team_lead_id in self.team_leads:
                    team_lead = self.team_leads[team_lead_id]
                    delegation = team_lead.delegate_task(
                        task_description=f"Sub-task: {task_id}",
                        task_parameters=task_info.get("parameters", {}),
                        required_capability=task_info.get("task_type", "general")
                    )
                    
                    if delegation:
                        if "active_delegations" not in state:
                            state["active_delegations"] = {}
                        state["active_delegations"][delegation.delegation_id] = delegation.dict()
        
        state["task_assignments"] = task_assignments
        state["status"] = "assigned"
        
        logger.info(f"Hierarchical Workflow: Assigned {len(task_assignments)} tasks to teams")
        return state
    
    def _parallel_execution_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Hierarchical Workflow: Executing tasks in parallel")
        
        state["status"] = "executing"
        
        # Process messages from team leads
        all_messages = []
        for team_lead in self.team_leads.values():
            messages = team_lead.process_incoming_messages()
            all_messages.extend(messages)
        
        # Update partial results
        if "partial_results" not in state:
            state["partial_results"] = {}
        
        # Simulate task execution and collect results
        # In a real implementation, this would coordinate with actual agents
        for task_id in state.get("task_assignments", {}).keys():
            if task_id not in state["partial_results"]:
                # Simulate task completion
                state["partial_results"][task_id] = {
                    "status": "completed",
                    "result": f"Mock result for {task_id}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        logger.info("Hierarchical Workflow: Parallel execution in progress")
        return state
    
    def _progress_monitor_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Hierarchical Workflow: Monitoring task progress")
        
        partial_results = state.get("partial_results", {})
        sub_tasks = state.get("sub_tasks", {})
        
        completed_tasks = [task_id for task_id, result in partial_results.items() 
                          if result.get("status") == "completed"]
        
        total_tasks = len(sub_tasks)
        completed_count = len(completed_tasks)
        
        # Check if all tasks are completed
        all_completed = completed_count == total_tasks
        state["all_tasks_completed"] = all_completed
        
        # Update progress metrics
        state["progress_metrics"] = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "progress_percentage": (completed_count / total_tasks * 100) if total_tasks > 0 else 100,
            "remaining_tasks": total_tasks - completed_count
        }
        
        logger.info(f"Hierarchical Workflow: Progress {completed_count}/{total_tasks} tasks completed")
        return state
    
    def _result_consolidator_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Hierarchical Workflow: Consolidating results")
        
        partial_results = state.get("partial_results", {})
        
        # Consolidate all results
        consolidated = {
            "workflow_summary": {
                "total_sub_tasks": len(partial_results),
                "execution_teams": list(set(task["team"] for task in state.get("sub_tasks", {}).values())),
                "consolidation_timestamp": datetime.utcnow().isoformat()
            },
            "task_results": partial_results,
            "team_performance": {}
        }
        
        # Add team performance metrics
        for team_id, team_lead in self.team_leads.items():
            team_status = team_lead.get_team_status()
            consolidated["team_performance"][team_id] = team_status
        
        state["consolidated_result"] = consolidated
        state["status"] = "consolidated"
        
        logger.info("Hierarchical Workflow: Results consolidated successfully")
        return state
    
    def _workflow_finalizer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Hierarchical Workflow: Finalizing execution")
        
        # Calculate execution time
        start_time_str = state.get("workflow_start_time")
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            state["workflow_end_time"] = end_time.isoformat()
            state["total_execution_time"] = execution_time
        
        state["status"] = "completed"
        
        # Add final summary to consolidated result
        if state.get("consolidated_result"):
            state["consolidated_result"]["execution_metrics"] = {
                "total_execution_time": state.get("total_execution_time", 0),
                "workflow_status": state["status"],
                "teams_involved": len(self.teams),
                "messages_processed": len(state.get("coordination_log", []))
            }
        
        logger.info("Hierarchical Workflow: Execution completed successfully")
        return state
    
    def get_system_status(self) -> Dict[str, Any]:
        team_statuses = {}
        for team_id, team_lead in self.team_leads.items():
            team_statuses[team_id] = team_lead.get_team_status()
        
        comm_stats = self.p2p_manager.get_communication_stats()
        
        return {
            "orchestrator_active": True,
            "total_teams": len(self.teams),
            "active_team_leads": len(self.team_leads),
            "total_agents": len(self.worker_agents),
            "team_statuses": team_statuses,
            "communication_stats": comm_stats,
            "system_capabilities": [
                cap for team in self.teams.values() 
                for cap in team.team_capabilities
            ]
        }
    
    def send_message(self, sender_id: str, recipient_id: str, content: Dict[str, Any], 
                    subject: str = "Hierarchical Communication") -> bool:
        try:
            message = AgentMessage(
                sender_id=sender_id,
                recipient_id=recipient_id,
                message_type=MessageType.COLLABORATION,
                subject=subject,
                content=content
            )
            
            return self.p2p_manager.send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send hierarchical message: {str(e)}")
            return False
    
    def broadcast_message(self, sender_id: str, content: Dict[str, Any], 
                         subject: str = "Team Broadcast") -> bool:
        try:
            return self.p2p_manager.broadcast_message(sender_id, content, subject)
            
        except Exception as e:
            logger.error(f"Failed to broadcast hierarchical message: {str(e)}")
            return False
    
    def route_message(self, message: AgentMessage, team_id: Optional[str] = None) -> bool:
        try:
            routing_rules = {}
            
            # Apply team-specific routing if specified
            if team_id and team_id in self.teams:
                team = self.teams[team_id]
                # Route to team supervisor if no specific recipient
                if message.recipient_id == "team":
                    routing_rules['target_agent'] = team.supervisor_id
            
            return self.p2p_manager.route_message(message, routing_rules)
            
        except Exception as e:
            logger.error(f"Failed to route hierarchical message: {str(e)}")
            return False
