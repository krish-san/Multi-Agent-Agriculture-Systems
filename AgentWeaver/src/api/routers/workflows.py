
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from src.api.models import (
    WorkflowCreateRequest,
    WorkflowControlRequest,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowStatus,
    ErrorResponse
)
from src.conditional_workflow import ConditionalWorkflowOrchestrator
from src.services.websocket_integration import integration_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/workflows", tags=["Workflows"])

# In-memory storage for workflow tracking (in production, use a database)
active_workflows: Dict[str, Dict[str, Any]] = {}
workflow_orchestrator = None


def get_orchestrator() -> ConditionalWorkflowOrchestrator:
    global workflow_orchestrator
    if workflow_orchestrator is None:
        workflow_orchestrator = ConditionalWorkflowOrchestrator()
        logger.info("Workflow orchestrator initialized")
    return workflow_orchestrator


def convert_workflow_to_response(workflow_data: Dict[str, Any]) -> WorkflowResponse:
    try:
        # Map internal status to API status enum
        internal_status = workflow_data.get("status", "pending")
        status_mapping = {
            "pending": WorkflowStatus.PENDING,
            "running": WorkflowStatus.RUNNING,
            "in_progress": WorkflowStatus.RUNNING,
            "completed": WorkflowStatus.COMPLETED,
            "failed": WorkflowStatus.FAILED,
            "error": WorkflowStatus.FAILED,
            "cancelled": WorkflowStatus.CANCELLED
        }
        status = status_mapping.get(internal_status, WorkflowStatus.PENDING)
        
        # Calculate progress based on status and steps
        progress = 0.0
        if status == WorkflowStatus.COMPLETED:
            progress = 1.0
        elif status == WorkflowStatus.RUNNING:
            completed_steps = workflow_data.get("completed_steps", [])
            total_steps = workflow_data.get("total_steps", 1)
            progress = len(completed_steps) / max(total_steps, 1)
        elif status == WorkflowStatus.FAILED:
            progress = workflow_data.get("progress", 0.0)
        
        # Parse timestamps
        created_at = workflow_data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        started_at = workflow_data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        
        completed_at = workflow_data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
        
        return WorkflowResponse(
            id=workflow_data.get("id"),
            status=status,
            created_at=created_at or datetime.now(),
            started_at=started_at,
            completed_at=completed_at,
            current_step=workflow_data.get("current_step"),
            progress=progress,
            assigned_agents=workflow_data.get("assigned_agents", []),
            input_data=workflow_data.get("input_data", {}),
            output_data=workflow_data.get("output_data"),
            error_message=workflow_data.get("error_message"),
            execution_time=workflow_data.get("execution_time"),
            metadata=workflow_data.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error converting workflow data to response: {e}")
        return WorkflowResponse(
            id=workflow_data.get("id", "unknown"),
            status=WorkflowStatus.FAILED,
            created_at=datetime.now(),
            progress=0.0,
            assigned_agents=[],
            input_data={},
            metadata={"conversion_error": str(e)}
        )


async def execute_workflow_async(workflow_id: str, workflow_request: WorkflowCreateRequest):
    try:
        logger.info(f"Starting background execution of workflow {workflow_id}")
        
        # Update workflow status to running
        if workflow_id in active_workflows:
            active_workflows[workflow_id].update({
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "current_step": "initializing"
            })
            
            # Notify WebSocket clients that workflow started
            await integration_service.notify_workflow_started(
                workflow_id, 
                active_workflows[workflow_id]
            )
        
        # Simulate workflow steps with notifications
        steps = ["text_analysis", "sentiment_detection", "data_processing", "result_generation"]
        
        for i, step in enumerate(steps):
            if workflow_id in active_workflows:
                active_workflows[workflow_id]["current_step"] = step
                
                # Notify step progress
                await integration_service.notify_workflow_step(
                    workflow_id, 
                    step, 
                    {"step_number": i + 1, "total_steps": len(steps)}
                )
                
                # Simulate step processing time
                await asyncio.sleep(1)
        
        # Get orchestrator and execute workflow
        orchestrator = get_orchestrator()
        
        # Create a unique thread ID for this workflow
        thread_id = f"workflow_{workflow_id}"
        
        # Execute the workflow
        result = orchestrator.execute_workflow(
            workflow_request.input_data,
            thread_id=thread_id
        )
        
        # Update workflow with results
        if workflow_id in active_workflows:
            active_workflows[workflow_id].update({
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "current_step": "completed",
                "progress": 1.0,
                "output_data": result,
                "execution_time": (datetime.now() - datetime.fromisoformat(
                    active_workflows[workflow_id]["started_at"]
                )).total_seconds()
            })
            
            # Notify WebSocket clients that workflow completed
            await integration_service.notify_workflow_completed(workflow_id, result)
        
        logger.info(f"Workflow {workflow_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        
        # Update workflow with error
        if workflow_id in active_workflows:
            active_workflows[workflow_id].update({
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error_message": str(e),
                "progress": 0.0
            })
            
            # Notify WebSocket clients that workflow failed
            await integration_service.notify_workflow_failed(
                workflow_id, 
                str(e), 
                {"error_type": type(e).__name__}
            )


@router.post("/", response_model=WorkflowResponse, status_code=202)
async def create_workflow(
    workflow_request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks
):
    try:
        # Generate unique workflow ID
        workflow_id = str(uuid.uuid4())
        
        logger.info(f"Creating new workflow {workflow_id} of type {workflow_request.workflow_type}")
        
        # Create workflow record
        workflow_data = {
            "id": workflow_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "current_step": "pending",
            "progress": 0.0,
            "assigned_agents": [],
            "input_data": workflow_request.input_data,
            "output_data": None,
            "error_message": None,
            "execution_time": None,
            "metadata": {
                "workflow_type": workflow_request.workflow_type,
                "priority": workflow_request.priority,
                "timeout": workflow_request.timeout,
                "agent_preferences": workflow_request.agent_preferences,
                "callback_url": workflow_request.callback_url,
                **workflow_request.metadata
            }
        }
        
        # Store workflow
        active_workflows[workflow_id] = workflow_data
        
        # Add background task to execute workflow
        background_tasks.add_task(execute_workflow_async, workflow_id, workflow_request)
        
        # Return immediate response
        response = convert_workflow_to_response(workflow_data)
        
        logger.info(f"Workflow {workflow_id} created and queued for execution")
        return response
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter workflows by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of workflows to return"),
    offset: int = Query(0, ge=0, description="Number of workflows to skip")
):
    try:
        logger.info(f"Listing workflows with status filter: {status}")
        
        # Get all workflows
        all_workflows = list(active_workflows.values())
        
        # Apply status filter
        if status:
            all_workflows = [w for w in all_workflows if w.get("status") == status]
        
        # Apply pagination
        total_count = len(all_workflows)
        paginated_workflows = all_workflows[offset:offset + limit]
        
        # Convert to response format
        workflow_responses = [convert_workflow_to_response(w) for w in paginated_workflows]
        
        # Calculate counts
        running_count = sum(1 for w in all_workflows if w.get("status") == "running")
        completed_count = sum(1 for w in all_workflows if w.get("status") == "completed")
        failed_count = sum(1 for w in all_workflows if w.get("status") == "failed")
        
        response = WorkflowListResponse(
            workflows=workflow_responses,
            total_count=total_count,
            running_count=running_count,
            completed_count=completed_count,
            failed_count=failed_count,
            metadata={
                "last_updated": datetime.now().isoformat(),
                "filters_applied": {"status": status},
                "pagination": {"limit": limit, "offset": offset}
            }
        )
        
        logger.info(f"Successfully listed {len(workflow_responses)} workflows")
        return response
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve workflows: {str(e)}"
        )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_details(workflow_id: str):
    try:
        logger.info(f"Getting details for workflow: {workflow_id}")
        
        # Check if workflow exists
        if workflow_id not in active_workflows:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_id}' not found"
            )
        
        workflow_data = active_workflows[workflow_id]
        response = convert_workflow_to_response(workflow_data)
        
        logger.info(f"Successfully retrieved details for workflow: {workflow_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting workflow details for {workflow_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve workflow details: {str(e)}"
        )


@router.post("/{workflow_id}/control")
async def control_workflow(
    workflow_id: str,
    control_request: WorkflowControlRequest
):
    try:
        logger.info(f"Controlling workflow {workflow_id}: {control_request.action}")
        
        # Check if workflow exists
        if workflow_id not in active_workflows:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_id}' not found"
            )
        
        workflow_data = active_workflows[workflow_id]
        current_status = workflow_data.get("status")
        
        # Validate control action based on current status
        if control_request.action == "cancel":
            if current_status in ["completed", "failed", "cancelled"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel workflow in status '{current_status}'"
                )
            workflow_data["status"] = "cancelled"
            workflow_data["completed_at"] = datetime.now().isoformat()
            workflow_data["error_message"] = control_request.reason or "Cancelled by user"
            
        elif control_request.action == "restart":
            workflow_data.update({
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "current_step": "pending",
                "progress": 0.0,
                "output_data": None,
                "error_message": None,
                "execution_time": None
            })
            
        elif control_request.action in ["pause", "resume"]:
            # Note: Actual pause/resume would require integration with the workflow engine
            logger.warning(f"Pause/resume not fully implemented for workflow {workflow_id}")
            workflow_data["metadata"]["last_control_action"] = {
                "action": control_request.action,
                "timestamp": datetime.now().isoformat(),
                "reason": control_request.reason
            }
        
        # Update metadata
        workflow_data["metadata"].update({
            "last_control_action": {
                "action": control_request.action,
                "timestamp": datetime.now().isoformat(),
                "reason": control_request.reason,
                **control_request.metadata
            }
        })
        
        response = convert_workflow_to_response(workflow_data)
        
        logger.info(f"Successfully applied {control_request.action} to workflow {workflow_id}")
        return {
            "message": f"Workflow {control_request.action} applied successfully",
            "workflow": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to control workflow: {str(e)}"
        )


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    try:
        logger.info(f"Deleting workflow: {workflow_id}")
        
        # Check if workflow exists
        if workflow_id not in active_workflows:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_id}' not found"
            )
        
        workflow_data = active_workflows[workflow_id]
        current_status = workflow_data.get("status")
        
        # Check if workflow can be deleted
        if current_status in ["running", "pending"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete workflow in status '{current_status}'. Cancel it first."
            )
        
        # Remove workflow
        del active_workflows[workflow_id]
        
        logger.info(f"Successfully deleted workflow: {workflow_id}")
        return {
            "message": f"Workflow '{workflow_id}' deleted successfully",
            "workflow_id": workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete workflow: {str(e)}"
        )
