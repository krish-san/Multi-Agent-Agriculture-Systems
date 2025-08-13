
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import logging
import uuid
from dataclasses import dataclass

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import Runnable

logger = logging.getLogger(__name__)


@dataclass
class ParallelExecutionState:
    parallel_task_id: str
    sub_tasks: List[Dict[str, Any]]
    completed_results: List[Dict[str, Any]]
    failed_tasks: List[Dict[str, Any]]
    execution_start_time: datetime
    current_batch_size: int = 3  # Max concurrent tasks
    
    def is_complete(self) -> bool:
        total_processed = len(self.completed_results) + len(self.failed_tasks)
        return total_processed >= len(self.sub_tasks)
    
    def get_progress(self) -> float:
        if not self.sub_tasks:
            return 1.0
        total_processed = len(self.completed_results) + len(self.failed_tasks)
        return total_processed / len(self.sub_tasks)


class ParallelForkNode:
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            sub_tasks = state.get("sub_tasks_to_process", [])
            
            if not sub_tasks:
                logger.warning("No sub-tasks provided for parallel execution")
                return self._create_empty_fork_result(state)
            
            # Create parallel execution state
            parallel_task_id = state.get("parallel_task_id") or str(uuid.uuid4())
            
            parallel_state = ParallelExecutionState(
                parallel_task_id=parallel_task_id,
                sub_tasks=sub_tasks,
                completed_results=[],
                failed_tasks=[],
                execution_start_time=datetime.utcnow(),
                current_batch_size=min(self.max_concurrent_tasks, len(sub_tasks))
            )
            
            # Update state with parallel execution information
            state.update({
                "parallel_task_id": parallel_task_id,
                "parallel_state": parallel_state,
                "parallel_execution_initiated": True,
                "total_subtasks": len(sub_tasks),
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "fork_timestamp": datetime.utcnow().isoformat(),
                "parallel_branches_created": True,
                "next_subtask_index": 0,  # Track which subtask to process next
                "active_subtasks": [],     # Track currently processing subtasks
                "fork_result": {
                    "success": True,
                    "parallel_task_id": parallel_task_id,
                    "subtasks_count": len(sub_tasks),
                    "max_concurrent": self.max_concurrent_tasks,
                    "message": f"Successfully forked execution for {len(sub_tasks)} sub-tasks"
                }
            })
            
            logger.info(f"Fork node: Created parallel execution for {len(sub_tasks)} sub-tasks with ID {parallel_task_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"Fork node failed: {str(e)}")
            return self._create_error_fork_result(state, str(e))
    
    def _create_empty_fork_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state.update({
            "parallel_execution_initiated": False,
            "fork_result": {
                "success": True,
                "subtasks_count": 0,
                "message": "No sub-tasks to process in parallel",
                "skip_parallel_execution": True
            }
        })
        return state
    
    def _create_error_fork_result(self, state: Dict[str, Any], error: str) -> Dict[str, Any]:
        state.update({
            "parallel_execution_initiated": False,
            "fork_result": {
                "success": False,
                "error": error,
                "message": f"Fork operation failed: {error}"
            }
        })
        return state


class ParallelWorkerNode:
    
    def __init__(self, agent_registry: Optional[Dict[str, Any]] = None, 
                 use_concurrent_adapters: bool = True):
        self.agent_registry = agent_registry or {}
        self.use_concurrent_adapters = use_concurrent_adapters
        
        # Initialize concurrent worker support if requested
        if use_concurrent_adapters:
            try:
                # Import here to avoid circular dependencies
                from .agents.concurrent_worker_adapter import get_global_worker_registry
                self.worker_registry = get_global_worker_registry()
                logger.info("ParallelWorkerNode initialized with concurrent adapter support")
            except ImportError as e:
                logger.warning(f"Could not load concurrent adapters: {e}")
                self.worker_registry = None
                self.use_concurrent_adapters = False
        else:
            self.worker_registry = None
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get next sub-task to process (works with or without parallel_state)
            next_subtask = self._get_next_subtask(state)
            if not next_subtask:
                # No more tasks to process
                return self._create_completion_result(state)
            
            # Execute the sub-task
            result = self._execute_subtask(next_subtask, state)
            
            # Update state with result
            return self._update_state_with_result(state, next_subtask, result)
            
        except Exception as e:
            logger.error(f"Worker node failed: {str(e)}")
            return self._create_worker_error(state, str(e))
    
    def _get_next_subtask(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sub_tasks = state.get("sub_tasks_to_process", [])
        next_index = state.get("next_subtask_index", 0)
        active_subtasks = state.get("active_subtasks", [])
        
        # Initialize if not set
        if "completed_subtask_results" not in state:
            state["completed_subtask_results"] = []
        if "failed_subtask_results" not in state:
            state["failed_subtask_results"] = []
        
        # Check if we've reached max concurrent tasks
        if len(active_subtasks) >= state.get("max_concurrent_tasks", 3):
            return None
        
        # Check if we have more tasks to process
        if next_index >= len(sub_tasks):
            return None
        
        # Get the next task
        next_task = sub_tasks[next_index].copy()
        next_task["worker_start_time"] = datetime.utcnow().isoformat()
        next_task["subtask_index"] = next_index
        
        # Update state to mark this task as being processed
        active_subtasks.append(next_task)
        state["active_subtasks"] = active_subtasks
        state["next_subtask_index"] = next_index + 1
        
        return next_task
    
    def _execute_subtask(self, subtask: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        task_id = subtask.get("task_id", f"subtask_{subtask.get('subtask_index', 'unknown')}")
        task_type = subtask.get("task_type", "general")
        parameters = subtask.get("parameters", {})
        
        logger.info(f"Worker executing sub-task {task_id} of type {task_type}")
        
        # Try using concurrent worker adapters first
        if self.use_concurrent_adapters and self.worker_registry:
            try:
                result = self.worker_registry.execute_subtask_with_best_adapter(
                    subtask, 
                    state.get("context", {})
                )
                
                # The concurrent adapter already formats the result properly
                if result.get("status") in ["completed", "failed"]:
                    logger.info(f"Sub-task {task_id} executed via concurrent adapter: {result.get('status')}")
                    return result
                
            except Exception as e:
                logger.warning(f"Concurrent adapter failed for {task_id}, falling back to legacy execution: {e}")
        
        # Fallback to legacy execution method
        agent = self._find_suitable_agent(subtask)
        
        try:
            # Simulate task execution based on type
            if task_type == "text_processing":
                result = self._execute_text_processing(parameters, agent)
            elif task_type == "data_analysis":
                result = self._execute_data_analysis(parameters, agent)
            elif task_type == "api_call":
                result = self._execute_api_call(parameters, agent)
            else:
                result = self._execute_generic_task(parameters, agent)
            
            result.update({
                "subtask_id": task_id,
                "agent_id": agent.get("agent_id", "mock_agent") if agent else "no_agent",
                "status": "completed",
                "execution_time": 1.0,  # Simulated execution time
                "completed_at": datetime.utcnow().isoformat(),
                "execution_method": "legacy_simulation"
            })
            
            logger.info(f"Sub-task {task_id} completed via legacy simulation")
            return result
            
        except Exception as e:
            logger.error(f"Sub-task {task_id} failed: {str(e)}")
            return {
                "subtask_id": task_id,
                "agent_id": agent.get("agent_id", "unknown") if agent else "unknown",
                "status": "failed",
                "error": str(e),
                "execution_time": 0.5,
                "completed_at": datetime.utcnow().isoformat(),
                "execution_method": "legacy_simulation"
            }
    
    def _execute_text_processing(self, parameters: Dict[str, Any], agent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        text_item = parameters.get("item", "")
        
        return {
            "processed_text": f"Processed: {text_item}",
            "original_length": len(str(text_item)),
            "processed_length": len(f"Processed: {text_item}"),
            "processing_type": "text_processing"
        }
    
    def _execute_data_analysis(self, parameters: Dict[str, Any], agent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        data_item = parameters.get("item", {})
        
        # Simulate analysis
        item_keys = list(data_item.keys()) if isinstance(data_item, dict) else []
        
        return {
            "analysis_result": f"Analyzed data with keys: {item_keys}",
            "data_points": len(item_keys),
            "analysis_type": "data_analysis",
            "insights": f"Found {len(item_keys)} data attributes"
        }
    
    def _execute_api_call(self, parameters: Dict[str, Any], agent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        endpoint = parameters.get("endpoint", "/unknown")
        method = parameters.get("method", "GET")
        
        # Simulate API call
        return {
            "api_response": f"Mock response from {method} {endpoint}",
            "status_code": 200,
            "response_time": 0.3,
            "api_call_type": "mock_api"
        }
    
    def _execute_generic_task(self, parameters: Dict[str, Any], agent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        item = parameters.get("item", "unknown_item")
        
        return {
            "processed_item": str(item),
            "processing_result": f"Generic processing of {item}",
            "task_type": "generic"
        }
    
    def _find_suitable_agent(self, subtask: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        required_capabilities = subtask.get("required_capabilities", [])
        
        # For demo purposes, return a mock agent
        if self.agent_registry:
            # In a real implementation, find agent with matching capabilities
            for agent_id, agent in self.agent_registry.items():
                if agent.get("status") == "available":
                    return {"agent_id": agent_id, "capabilities": agent.get("capabilities", [])}
        
        # Return mock agent if no real agents available
        return {
            "agent_id": "mock_worker_agent",
            "capabilities": required_capabilities or ["general"]
        }
    
    def _update_state_with_result(self, state: Dict[str, Any], subtask: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        parallel_state = state.get("parallel_state")
        
        # Remove from active tasks
        active_subtasks = state.get("active_subtasks", [])
        active_subtasks = [t for t in active_subtasks if t.get("subtask_index") != subtask.get("subtask_index")]
        state["active_subtasks"] = active_subtasks
        
        # Add to completed or failed results
        if result.get("status") == "completed":
            completed_results = state.get("completed_subtask_results", [])
            completed_results.append(result)
            state["completed_subtask_results"] = completed_results
            
            if parallel_state:
                parallel_state.completed_results.append(result)
        else:
            failed_results = state.get("failed_subtask_results", [])
            failed_results.append(result)
            state["failed_subtask_results"] = failed_results
            
            if parallel_state:
                parallel_state.failed_tasks.append(result)
        
        # Update execution status
        total_processed = len(state.get("completed_subtask_results", [])) + len(state.get("failed_subtask_results", []))
        total_subtasks = state.get("total_subtasks", 0)
        
        state.update({
            "subtasks_processed": total_processed,
            "execution_progress": total_processed / total_subtasks if total_subtasks > 0 else 1.0,
            "last_subtask_result": result,
            "worker_execution_timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Worker node: Processed {total_processed}/{total_subtasks} sub-tasks")
        
        return state
    
    def _create_completion_result(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state.update({
            "worker_completion": True,
            "message": "Worker completed all available sub-tasks"
        })
        return state
    
    def _create_worker_error(self, state: Dict[str, Any], error: str) -> Dict[str, Any]:
        state.update({
            "worker_error": True,
            "worker_error_message": error,
            "message": f"Worker execution failed: {error}"
        })
        return state


class ParallelAggregatorNode:
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Support both naming conventions for flexibility
            completed_results = state.get("completed_subtask_results", [])
            failed_results = state.get("failed_subtask_results", [])
            
            # Also check for 'processed_results' field as mentioned in task description
            processed_results = state.get("processed_results", [])
            if processed_results and not completed_results:
                completed_results = processed_results
            
            original_task = state.get("original_task_data", {})
            parallel_task_id = state.get("parallel_task_id")
            
            total_subtasks = len(completed_results) + len(failed_results)
            
            if total_subtasks == 0:
                return self._create_empty_aggregation(state)
            
            # Create aggregated result
            aggregated_result = self._aggregate_results(completed_results, failed_results, original_task)
            
            # Update state with final result
            state.update({
                "final_aggregated_result": aggregated_result,
                "parallel_execution_completed": True,
                "aggregation_timestamp": datetime.utcnow().isoformat(),
                "aggregation_result": {
                    "success": True,
                    "parallel_task_id": parallel_task_id,
                    "total_subtasks": total_subtasks,
                    "successful_subtasks": len(completed_results),
                    "failed_subtasks": len(failed_results),
                    "final_result": aggregated_result,
                    "message": f"Successfully aggregated {total_subtasks} sub-task results"
                },
                # Add consolidated final response for easy consumption
                "final_consolidated_response": self._create_final_response(aggregated_result, original_task)
            })
            
            logger.info(f"Aggregator: Combined {len(completed_results)} successful and {len(failed_results)} failed sub-tasks")
            
            return state
            
        except Exception as e:
            logger.error(f"Aggregator node failed: {str(e)}")
            return self._create_aggregation_error(state, str(e))
    
    def _aggregate_results(self, completed: List[Dict[str, Any]], failed: List[Dict[str, Any]], original_task: Dict[str, Any]) -> Dict[str, Any]:
        
        total_tasks = len(completed) + len(failed)
        success_rate = len(completed) / total_tasks if total_tasks > 0 else 0
        
        # Calculate execution metrics
        execution_times = [r.get("execution_time", 0) for r in completed + failed]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        total_execution_time = sum(execution_times)
        
        # Aggregate task-specific results
        task_type = original_task.get("task_type", "general")
        aggregated_data = self._aggregate_by_task_type(completed, task_type)
        
        # Build final result
        return {
            "status": "completed" if len(failed) == 0 else "partially_completed",
            "parallel_execution": True,
            "execution_summary": {
                "total_subtasks": total_tasks,
                "successful_subtasks": len(completed),
                "failed_subtasks": len(failed),
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "total_execution_time": total_execution_time
            },
            "aggregated_data": aggregated_data,
            "individual_results": completed,
            "failed_tasks": failed,
            "original_task_type": task_type,
            "aggregated_at": datetime.utcnow().isoformat()
        }
    
    def _aggregate_by_task_type(self, completed_results: List[Dict[str, Any]], task_type: str) -> Dict[str, Any]:
        
        if task_type == "text_processing":
            total_original_length = sum(r.get("original_length", 0) for r in completed_results)
            total_processed_length = sum(r.get("processed_length", 0) for r in completed_results)
            processed_texts = [r.get("processed_text", "") for r in completed_results]
            
            # Consolidate all processed texts into a final document
            consolidated_text = "\n\n".join(filter(None, processed_texts))
            
            return {
                "total_texts_processed": len(processed_texts),
                "total_original_characters": total_original_length,
                "total_processed_characters": total_processed_length,
                "average_text_length": total_original_length / len(completed_results) if completed_results else 0,
                "consolidated_output": consolidated_text,
                "processing_efficiency": total_processed_length / total_original_length if total_original_length > 0 else 0
            }
            
        elif task_type == "data_analysis":
            total_data_points = sum(r.get("data_points", 0) for r in completed_results)
            insights = [r.get("insights", "") for r in completed_results]
            
            # Consolidate insights into a comprehensive summary
            consolidated_insights = "AGGREGATED ANALYSIS INSIGHTS:\n" + "\n".join(f"• {insight}" for insight in insights if insight)
            
            return {
                "total_data_points_analyzed": total_data_points,
                "total_analyses_performed": len(completed_results),
                "insights_generated": insights,
                "average_data_points_per_analysis": total_data_points / len(completed_results) if completed_results else 0,
                "consolidated_insights": consolidated_insights,
                "analysis_coverage": len(completed_results)
            }
            
        elif task_type == "api_call":
            successful_calls = [r for r in completed_results if r.get("status_code", 0) == 200]
            response_times = [r.get("response_time", 0) for r in completed_results]
            
            # Consolidate API responses
            all_responses = []
            for result in completed_results:
                if "response_data" in result:
                    all_responses.append(result["response_data"])
            
            return {
                "total_api_calls": len(completed_results),
                "successful_calls": len(successful_calls),
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "api_success_rate": len(successful_calls) / len(completed_results) if completed_results else 0,
                "consolidated_responses": all_responses,
                "total_response_data_points": len(all_responses)
            }
            
        else:
            # Generic aggregation with enhanced consolidation
            processed_items = [r.get("processed_item", "") for r in completed_results]
            results_summary = [r.get("result", "") for r in completed_results]
            
            # Create a consolidated summary
            consolidated_summary = f"PARALLEL EXECUTION SUMMARY ({task_type.upper()}):\n"
            consolidated_summary += f"Total items processed: {len(processed_items)}\n"
            for i, result in enumerate(results_summary, 1):
                if result:
                    consolidated_summary += f"{i}. {result}\n"
            
            return {
                "total_items_processed": len(processed_items),
                "processing_type": task_type,
                "processed_items": processed_items,
                "results_summary": results_summary,
                "consolidated_summary": consolidated_summary,
                "completion_rate": len([item for item in processed_items if item]) / len(processed_items) if processed_items else 0
            }
    
    def _create_empty_aggregation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state.update({
            "final_aggregated_result": {
                "status": "no_results",
                "message": "No sub-task results to aggregate"
            },
            "aggregation_result": {
                "success": True,
                "message": "No results to aggregate"
            }
        })
        return state
    
    def _create_aggregation_error(self, state: Dict[str, Any], error: str) -> Dict[str, Any]:
        state.update({
            "aggregation_result": {
                "success": False,
                "error": error,
                "message": f"Aggregation failed: {error}"
            }
        })
        return state
    
    def _create_final_response(self, aggregated_result: Dict[str, Any], original_task: Dict[str, Any]) -> str:
        task_type = original_task.get("task_type", "general")
        execution_summary = aggregated_result.get("execution_summary", {})
        aggregated_data = aggregated_result.get("aggregated_data", {})
        
        # Build a comprehensive final response
        response_parts = []
        
        # Header with execution summary
        response_parts.append(f"PARALLEL EXECUTION COMPLETE - {task_type.upper()}")
        response_parts.append("=" * 50)
        response_parts.append(f"Status: {aggregated_result.get('status', 'unknown').title()}")
        response_parts.append(f"Total Sub-tasks: {execution_summary.get('total_subtasks', 0)}")
        response_parts.append(f"Successful: {execution_summary.get('successful_subtasks', 0)}")
        response_parts.append(f"Failed: {execution_summary.get('failed_subtasks', 0)}")
        response_parts.append(f"Success Rate: {execution_summary.get('success_rate', 0):.1%}")
        response_parts.append(f"Total Execution Time: {execution_summary.get('total_execution_time', 0):.2f}s")
        response_parts.append("")
        
        # Task-specific consolidated results
        if "consolidated_output" in aggregated_data:
            response_parts.append("CONSOLIDATED OUTPUT:")
            response_parts.append("-" * 20)
            response_parts.append(aggregated_data["consolidated_output"])
            response_parts.append("")
        
        elif "consolidated_insights" in aggregated_data:
            response_parts.append(aggregated_data["consolidated_insights"])
            response_parts.append("")
            
        elif "consolidated_responses" in aggregated_data:
            response_parts.append("API RESPONSES SUMMARY:")
            response_parts.append("-" * 20)
            response_parts.append(f"Total API calls made: {aggregated_data.get('total_api_calls', 0)}")
            response_parts.append(f"Successful calls: {aggregated_data.get('successful_calls', 0)}")
            response_parts.append(f"Average response time: {aggregated_data.get('average_response_time', 0):.3f}s")
            response_parts.append("")
            
        elif "consolidated_summary" in aggregated_data:
            response_parts.append(aggregated_data["consolidated_summary"])
            response_parts.append("")
        
        # Performance metrics
        response_parts.append("PERFORMANCE METRICS:")
        response_parts.append("-" * 20)
        
        if task_type == "text_processing":
            response_parts.append(f"Characters processed: {aggregated_data.get('total_processed_characters', 0):,}")
            response_parts.append(f"Processing efficiency: {aggregated_data.get('processing_efficiency', 0):.1%}")
        elif task_type == "data_analysis":
            response_parts.append(f"Data points analyzed: {aggregated_data.get('total_data_points_analyzed', 0):,}")
            response_parts.append(f"Analysis coverage: {aggregated_data.get('analysis_coverage', 0)} datasets")
        elif task_type == "api_call":
            response_parts.append(f"API success rate: {aggregated_data.get('api_success_rate', 0):.1%}")
            response_parts.append(f"Response data points: {aggregated_data.get('total_response_data_points', 0)}")
        
        response_parts.append(f"Average execution time per task: {execution_summary.get('average_execution_time', 0):.2f}s")
        
        # Footer with completion timestamp
        response_parts.append("")
        response_parts.append(f"Aggregation completed at: {aggregated_result.get('aggregated_at', 'unknown')}")
        
        return "\n".join(response_parts)


def create_parallel_execution_router(state: Dict[str, Any]) -> str:
    
    # Check if fork operation completed successfully
    if not state.get("parallel_execution_initiated", False):
        logger.info("Router: Fork operation not initiated, routing to aggregator")
        return "aggregator"
    
    # Check if we should skip parallel execution (no sub-tasks)
    if state.get("fork_result", {}).get("skip_parallel_execution", False):
        logger.info("Router: Parallel execution skipped, routing to aggregator")
        return "aggregator"
    
    # Get task counts for routing decision
    total_subtasks = state.get("total_subtasks", 0)
    subtasks_processed = state.get("subtasks_processed", 0)
    active_subtasks = len(state.get("active_subtasks", []))
    next_subtask_index = state.get("next_subtask_index", 0)
    
    # Support both field naming conventions for flexibility
    completed_results = state.get("completed_subtask_results", [])
    failed_results = state.get("failed_subtask_results", [])
    
    # Also check for the field name mentioned in Task 12.5 description
    processed_results = state.get("processed_results", [])
    sub_tasks_to_process = state.get("sub_tasks_to_process", [])
    
    # If using the alternative field names, calculate totals
    if processed_results and sub_tasks_to_process:
        total_results = len(processed_results) + len(failed_results)
        total_tasks_to_process = len(sub_tasks_to_process)
        
        # Task 12.5 requirement: Check if processed_results matches sub_tasks_to_process
        if total_results >= total_tasks_to_process:
            logger.info(f"Router: All tasks complete - {total_results}/{total_tasks_to_process} processed, routing to aggregator")
            return "aggregator"
    else:
        # Use the standard field names
        total_results = len(completed_results) + len(failed_results)
        
        # Check if all tasks are complete using multiple criteria
        all_tasks_complete = (
            (subtasks_processed >= total_subtasks) and
            (total_results >= total_subtasks) and
            (active_subtasks == 0) and
            (next_subtask_index >= total_subtasks)
        )
        
        if all_tasks_complete:
            logger.info(f"Router: All subtasks complete - {total_results}/{total_subtasks} processed, routing to aggregator")
            return "aggregator"
    
    # Check if we have more tasks to start or tasks still running
    if (next_subtask_index < total_subtasks) or (active_subtasks > 0) or (subtasks_processed < total_subtasks):
        logger.debug(f"Router: Continuing parallel execution - next_index: {next_subtask_index}/{total_subtasks}, "
                    f"active: {active_subtasks}, processed: {subtasks_processed}")
        return "worker"
    
    # Fallback to aggregator if all conditions suggest completion
    logger.info("Router: Fallback routing to aggregator")
    return "aggregator"
