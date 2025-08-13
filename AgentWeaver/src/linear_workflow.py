
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import logging
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .core.models import Task, TaskStatus, AgentCapability
from .agents import TextAnalysisAgent, APIInteractionAgent, DataProcessingAgent

logger = logging.getLogger(__name__)


class WorkflowState(BaseModel):
    
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str = "Basic Linear Workflow"
    
    initial_input: Dict[str, Any] = Field(default_factory=dict)
    
    current_step: str = "start"
    completed_steps: List[str] = Field(default_factory=list)
    step_results: Dict[str, Any] = Field(default_factory=dict)
    
    step1_data: Optional[Dict[str, Any]] = None
    step2_data: Optional[Dict[str, Any]] = None
    final_result: Optional[Dict[str, Any]] = None
    
    error_occurred: bool = False
    error_message: Optional[str] = None
    error_step: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    workflow_start_time: datetime = Field(default_factory=datetime.utcnow)
    workflow_end_time: Optional[datetime] = None
    total_execution_time: Optional[float] = None
    
    status: str = "running"
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LinearWorkflowOrchestrator:
    
    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        self.checkpointer = checkpointer or MemorySaver()
        self.worker_agents = self._initialize_worker_agents()
        self.workflow_graph = None
        self._setup_workflow_graph()
        
        logger.info("Linear Workflow Orchestrator initialized")
    
    def _initialize_worker_agents(self) -> Dict[str, Any]:
        return {
            "text_analyzer": TextAnalysisAgent("WorkflowTextAnalyzer"),
            "api_client": APIInteractionAgent("WorkflowAPIClient"),
            "data_processor": DataProcessingAgent("WorkflowDataProcessor")
        }
    
    def _setup_workflow_graph(self):
        graph = StateGraph(dict)
        
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("step1_text_analysis", self._step1_text_analysis_node)
        graph.add_node("step2_data_enrichment", self._step2_data_enrichment_node)
        graph.add_node("step3_final_processing", self._step3_final_processing_node)
        graph.add_node("error_handler", self._error_handler_node)
        graph.add_node("workflow_finalizer", self._workflow_finalizer_node)
        
        graph.add_edge(START, "supervisor")
        
        def route_from_supervisor(state: Dict[str, Any]) -> str:
            if state.get("error_occurred"):
                return "error_handler"
            return "step1_text_analysis"
        
        graph.add_conditional_edges(
            "supervisor",
            route_from_supervisor,
            {
                "step1_text_analysis": "step1_text_analysis",
                "error_handler": "error_handler"
            }
        )
        
        def route_from_step1(state: Dict[str, Any]) -> str:
            return "error_handler" if state.get("error_occurred") else "step2_data_enrichment"
        
        def route_from_step2(state: Dict[str, Any]) -> str:
            return "error_handler" if state.get("error_occurred") else "step3_final_processing"
        
        def route_from_step3(state: Dict[str, Any]) -> str:
            return "error_handler" if state.get("error_occurred") else "workflow_finalizer"
        
        graph.add_conditional_edges(
            "step1_text_analysis",
            route_from_step1,
            {
                "step2_data_enrichment": "step2_data_enrichment",
                "error_handler": "error_handler"
            }
        )
        
        graph.add_conditional_edges(
            "step2_data_enrichment", 
            route_from_step2,
            {
                "step3_final_processing": "step3_final_processing",
                "error_handler": "error_handler"
            }
        )
        
        graph.add_conditional_edges(
            "step3_final_processing",
            route_from_step3,
            {
                "workflow_finalizer": "workflow_finalizer",
                "error_handler": "error_handler"
            }
        )
        
        graph.add_edge("error_handler", "workflow_finalizer")
        graph.add_edge("workflow_finalizer", END)
        
        self.workflow_graph = graph.compile(checkpointer=self.checkpointer)
        
        logger.info("Linear workflow graph compiled successfully")
    
    def _supervisor_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Supervisor: Validating workflow input and setting up execution")
            
            state["current_step"] = "supervisor"
            state["completed_steps"] = []
            state["step_results"] = {}
            state["workflow_start_time"] = datetime.utcnow().isoformat()
            state["status"] = "running"
            state["error_occurred"] = False
            
            if not state.get("initial_input"):
                raise ValueError("No initial input provided for workflow")
            
            state["completed_steps"].append("supervisor")
            state["step_results"]["supervisor"] = {
                "action": "input_validation",
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Supervisor: Input validation completed, proceeding to Step 1")
            
        except Exception as e:
            logger.error(f"Supervisor: Validation failed - {str(e)}")
            state["error_occurred"] = True
            state["error_message"] = f"Supervisor validation failed: {str(e)}"
            state["error_step"] = "supervisor"
            state["status"] = "failed"
            if "workflow_start_time" not in state:
                state["workflow_start_time"] = datetime.utcnow().isoformat()
        
        return state
    
    def _step1_text_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Step 1: Starting text analysis")
            state["current_step"] = "step1_text_analysis"
            
            input_data = state.get("initial_input", {})
            text_content = input_data.get("text", "")
            
            if not text_content:
                raise ValueError("No text content provided for analysis")
            
            task = Task(
                task_id=f"step1_{state.get('workflow_id', 'unknown')}",
                title="Workflow Step 1: Text Analysis",
                task_type="text_analysis",
                parameters={
                    "text": text_content,
                    "analysis_type": "summarize"
                }
            )
            
            text_agent = self.worker_agents["text_analyzer"]
            result = text_agent.execute(task, state)
            
            state["step1_data"] = result
            state["completed_steps"].append("step1_text_analysis")
            state["step_results"]["step1_text_analysis"] = {
                "agent": "text_analyzer",
                "result": result,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Step 1: Text analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Step 1: Text analysis failed - {str(e)}")
            state["error_occurred"] = True
            state["error_message"] = f"Step 1 text analysis failed: {str(e)}"
            state["error_step"] = "step1_text_analysis"
            state["error_details"] = {"exception_type": type(e).__name__}
            state["status"] = "failed"
        
        return state
    
    def _step2_data_enrichment_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Step 2: Starting data enrichment")
            state["current_step"] = "step2_data_enrichment"
            
            # Get data from step 1
            step1_result = state.get("step1_data", {})
            
            # Create task for API interaction (enrichment)
            task = Task(
                task_id=f"step2_{state.get('workflow_id', 'unknown')}",
                title="Workflow Step 2: Data Enrichment",
                task_type="api_request",
                parameters={
                    "url": "https://httpbin.org/json",  # Test API
                    "method": "GET"
                }
            )
            
            # Execute API interaction
            api_agent = self.worker_agents["api_client"]
            result = api_agent.execute(task, state)
            
            # Check if API call failed
            if result.get("error") or not result.get("success", True):
                error_msg = result.get("error", "API call failed")
                raise Exception(error_msg)
            
            # Combine with previous results
            enriched_data = {
                "text_analysis": step1_result,
                "external_data": result,
                "enrichment_timestamp": datetime.utcnow().isoformat()
            }
            
            # Store results
            state["step2_data"] = enriched_data
            state["completed_steps"].append("step2_data_enrichment")
            state["step_results"]["step2_data_enrichment"] = {
                "agent": "api_client",
                "result": enriched_data,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Step 2: Data enrichment completed successfully")
            
        except Exception as e:
            logger.error(f"Step 2: Data enrichment failed - {str(e)}")
            state["error_occurred"] = True
            state["error_message"] = f"Step 2 data enrichment failed: {str(e)}"
            state["error_step"] = "step2_data_enrichment"
            state["error_details"] = {"exception_type": type(e).__name__}
            state["status"] = "failed"
        
        return state
    
    def _step3_final_processing_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Step 3: Starting final processing")
            state["current_step"] = "step3_final_processing"
            
            # Get numeric data for processing (from initial input or generate some)
            input_data = state.get("initial_input", {})
            numeric_data = input_data.get("numbers", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            
            # Create task for data processing
            task = Task(
                task_id=f"step3_{state.get('workflow_id', 'unknown')}",
                title="Workflow Step 3: Final Processing",
                task_type="data_processing",
                parameters={
                    "data": numeric_data,
                    "operation": "calculate_statistics"
                }
            )
            
            # Execute data processing
            data_agent = self.worker_agents["data_processor"]
            result = data_agent.execute(task, state)
            
            # Create final comprehensive result
            final_result = {
                "workflow_summary": {
                    "text_analysis": state.get("step1_data", {}),
                    "data_enrichment": state.get("step2_data", {}),
                    "statistical_analysis": result
                },
                "workflow_metadata": {
                    "workflow_id": state.get("workflow_id"),
                    "total_steps": 3,
                    "completed_steps": len(state.get("completed_steps", [])) + 1,
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Store results
            state["final_result"] = final_result
            state["completed_steps"].append("step3_final_processing")
            state["step_results"]["step3_final_processing"] = {
                "agent": "data_processor",
                "result": result,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Step 3: Final processing completed successfully")
            
        except Exception as e:
            logger.error(f"Step 3: Final processing failed - {str(e)}")
            state["error_occurred"] = True
            state["error_message"] = f"Step 3 final processing failed: {str(e)}"
            state["error_step"] = "step3_final_processing"
            state["error_details"] = {"exception_type": type(e).__name__}
            state["status"] = "failed"
        
        return state
    
    def _error_handler_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.error(f"Error Handler: Processing error in step {state.get('error_step')}")
            
            # Log comprehensive error information
            error_summary = {
                "error_step": state.get("error_step"),
                "error_message": state.get("error_message"),
                "error_details": state.get("error_details", {}),
                "completed_steps": state.get("completed_steps", []),
                "partial_results": state.get("step_results", {}),
                "error_timestamp": datetime.utcnow().isoformat()
            }
            
            # Create error result
            state["final_result"] = {
                "workflow_status": "failed",
                "error_summary": error_summary,
                "partial_data": {
                    "step1_data": state.get("step1_data"),
                    "step2_data": state.get("step2_data")
                }
            }
            
            state["status"] = "failed"
            logger.error(f"Error Handler: Error processing completed")
            
        except Exception as e:
            logger.critical(f"Error Handler: Critical failure in error handling - {str(e)}")
            state["error_message"] = f"Critical error handling failure: {str(e)}"
        
        return state
    
    def _workflow_finalizer_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.info("Workflow Finalizer: Completing workflow execution")
            
            # Calculate timing
            start_time_str = state.get("workflow_start_time")
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds()
                
                # Update final state
                state["workflow_end_time"] = end_time.isoformat()
                state["total_execution_time"] = execution_time
            else:
                # Fallback if start time missing
                state["workflow_end_time"] = datetime.utcnow().isoformat()
                state["total_execution_time"] = 0.0
                execution_time = 0.0
            
            # Set final status if not already failed
            if state.get("status") != "failed":
                state["status"] = "completed"
            
            # Add completion summary to final result
            if state.get("final_result"):
                state["final_result"]["execution_metrics"] = {
                    "total_execution_time": execution_time,
                    "steps_completed": len(state.get("completed_steps", [])),
                    "workflow_status": state["status"]
                }
            
            logger.info(f"Workflow Finalizer: Workflow {state['status']} in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Workflow Finalizer: Finalization failed - {str(e)}")
            state["error_occurred"] = True
            state["error_message"] = f"Workflow finalization failed: {str(e)}"
            # Ensure we have basic timing info even on error
            if "workflow_end_time" not in state:
                state["workflow_end_time"] = datetime.utcnow().isoformat()
            if "total_execution_time" not in state:
                state["total_execution_time"] = 0.0
        
        return state
    
    def execute_workflow(self, input_data: Dict[str, Any], thread_id: str = "workflow") -> Dict[str, Any]:
        try:
            initial_state = {
                "initial_input": input_data,
                "workflow_id": str(uuid.uuid4()),
                "workflow_name": "Basic Linear Workflow"
            }
            
            config = {"configurable": {"thread_id": thread_id}}
            final_state = self.workflow_graph.invoke(initial_state, config)
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "status": "critical_failure",
                "error_message": f"Workflow execution failed: {str(e)}",
                "final_result": None
            }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        return {
            "orchestrator_active": True,
            "workflow_graph_compiled": self.workflow_graph is not None,
            "available_agents": len(self.worker_agents),
            "agent_status": {
                name: agent.status.value
                for name, agent in self.worker_agents.items()
            }
        }
    
    def add_step(self, step_name: str, agent_name: str, step_config: Dict[str, Any] = None) -> bool:
        try:
            if step_config is None:
                step_config = {}
            
            # Check if agent exists
            if agent_name not in self.worker_agents:
                logger.error(f"Agent {agent_name} not found for step {step_name}")
                return False
            
            # For linear workflows, we'd need to rebuild the graph
            # This is a simplified implementation
            logger.info(f"Step {step_name} would be added with agent {agent_name}")
            logger.warning("Dynamic step addition requires workflow graph rebuild")
            
            # Store step configuration for potential future use
            if not hasattr(self, 'custom_steps'):
                self.custom_steps = {}
            
            self.custom_steps[step_name] = {
                'agent_name': agent_name,
                'config': step_config,
                'added_at': datetime.utcnow().isoformat()
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add step {step_name}: {str(e)}")
            return False
    
    def get_status(self, workflow_id: str = None) -> Dict[str, Any]:
        try:
            base_status = {
                'orchestrator_status': 'active',
                'total_agents': len(self.worker_agents),
                'workflow_graph_ready': self.workflow_graph is not None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add agent-specific status
            agent_statuses = {}
            for name, agent in self.worker_agents.items():
                agent_statuses[name] = {
                    'status': agent.status.value,
                    'capabilities': [cap.value for cap in agent.capabilities],
                    'current_task': getattr(agent.agent_state, 'current_task_id', None)
                }
            
            base_status['agents'] = agent_statuses
            
            # Add custom steps if any
            if hasattr(self, 'custom_steps'):
                base_status['custom_steps'] = len(self.custom_steps)
            
            # If specific workflow_id requested, this would query that workflow's state
            # For now, return general status
            if workflow_id:
                base_status['requested_workflow_id'] = workflow_id
                base_status['note'] = 'Specific workflow status tracking not implemented'
            
            return base_status
            
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}")
            return {
                'orchestrator_status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
