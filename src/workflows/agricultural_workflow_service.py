"""
Agricultural Workflow Execution Service

This module provides the core functionality for executing agricultural workflows
consisting of multiple agent-driven steps.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio
import logging
import json
import os
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep:
    """Represents a single step in an agricultural workflow."""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        agent: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        self.id = step_id
        self.name = name
        self.agent = agent
        self.description = description
        self.parameters = parameters or {}
        self.status = StepStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.output = None
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary representation for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "agent": self.agent,
            "status": self.status,
            "description": self.description,
            "parameters": self.parameters,
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "output": self.output,
            "error": self.error
        }


class AgriculturalWorkflow:
    """Represents a complete agricultural workflow with multiple steps."""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = workflow_id
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.status = WorkflowStatus.PENDING
        self.progress = 0.0
        self.start_time = None
        self.end_time = None
        self.total_duration = None
        self.metadata = metadata or {}
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps.append(step)
    
    def update_progress(self) -> None:
        """Update workflow progress based on step statuses."""
        if not self.steps:
            self.progress = 0.0
            return
            
        completed_steps = sum(1 for step in self.steps 
                            if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED])
        self.progress = completed_steps / len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary representation for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "progress": self.progress,
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "totalDuration": self.total_duration,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": self.metadata
        }


class WorkflowExecutionEngine:
    """Engine responsible for executing agricultural workflows."""
    
    def __init__(self):
        self.active_workflows: Dict[str, AgriculturalWorkflow] = {}
        self.agent_registry = {}  # In a real implementation, this would map agent IDs to actual agent instances
    
    def register_workflow(self, workflow: AgriculturalWorkflow) -> None:
        """Register a workflow with the execution engine."""
        self.active_workflows[workflow.id] = workflow
        logger.info(f"Workflow registered: {workflow.id} - {workflow.name}")
    
    def get_workflow(self, workflow_id: str) -> Optional[AgriculturalWorkflow]:
        """Get a workflow by ID."""
        return self.active_workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows."""
        return [workflow.to_dict() for workflow in self.active_workflows.values()]
    
    async def execute_workflow(self, workflow_id: str) -> None:
        """Execute a workflow by ID."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            logger.error(f"Workflow not found: {workflow_id}")
            return
        
        # Set workflow to running
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now()
        logger.info(f"Starting workflow execution: {workflow.name} (ID: {workflow.id})")
        
        try:
            # Execute each step in sequence
            for step in workflow.steps:
                if workflow.status != WorkflowStatus.RUNNING:
                    # Workflow was cancelled or paused
                    break
                
                await self._execute_step(workflow, step)
                workflow.update_progress()
                
            # If all steps completed and workflow is still running, mark as completed
            if (workflow.status == WorkflowStatus.RUNNING and 
                all(step.status == StepStatus.COMPLETED for step in workflow.steps)):
                workflow.status = WorkflowStatus.COMPLETED
                
        except Exception as e:
            logger.error(f"Error executing workflow {workflow.id}: {str(e)}")
            workflow.status = WorkflowStatus.FAILED
        finally:
            workflow.end_time = datetime.now()
            if workflow.start_time:
                workflow.total_duration = int((workflow.end_time - workflow.start_time).total_seconds() * 1000)
            logger.info(f"Workflow execution finished: {workflow.name} (Status: {workflow.status})")
    
    async def _execute_step(self, workflow: AgriculturalWorkflow, step: WorkflowStep) -> None:
        """Execute a single workflow step."""
        step.status = StepStatus.IN_PROGRESS
        step.start_time = datetime.now()
        logger.info(f"Executing step: {step.name} with agent {step.agent}")
        
        try:
            # In a real implementation, this would call the actual agent
            # For demonstration, we'll simulate agent execution
            agent_result = await self._simulate_agent_execution(step.agent, step.parameters)
            
            step.output = agent_result.get('output')
            step.status = StepStatus.COMPLETED
        except Exception as e:
            logger.error(f"Error executing step {step.id} in workflow {workflow.id}: {str(e)}")
            step.error = str(e)
            step.status = StepStatus.FAILED
            # If a step fails, mark the workflow as failed unless it's a non-critical step
            if not step.parameters.get('optional', False):
                workflow.status = WorkflowStatus.FAILED
        finally:
            step.end_time = datetime.now()
            if step.start_time:
                step.duration = int((step.end_time - step.start_time).total_seconds() * 1000)
    
    async def _simulate_agent_execution(self, agent_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate agent execution (for demonstration purposes)."""
        # In a real implementation, this would call the actual agent
        # For now, we'll just sleep for a random amount of time and return some sample data
        execution_time = 2 + (hash(agent_id) % 5)  # 2-7 seconds
        await asyncio.sleep(execution_time)
        
        # Simulate agent failure occasionally
        if hash(agent_id + str(parameters)) % 15 == 0:
            raise Exception(f"Simulated agent failure for {agent_id}")
            
        return {
            "output": f"Agent {agent_id} successfully executed with parameters: {json.dumps(parameters)}. "
                     f"Simulated execution time: {execution_time} seconds."
        }
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return False
        
        workflow.status = WorkflowStatus.PENDING
        logger.info(f"Workflow paused: {workflow.name} (ID: {workflow.id})")
        return True
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED]:
            return False
        
        workflow.status = WorkflowStatus.CANCELLED
        workflow.end_time = datetime.now()
        if workflow.start_time:
            workflow.total_duration = int((workflow.end_time - workflow.start_time).total_seconds() * 1000)
        logger.info(f"Workflow cancelled: {workflow.name} (ID: {workflow.id})")
        return True


# Example usage
async def create_and_run_sample_workflow():
    """Create and run a sample agricultural workflow for demonstration."""
    engine = WorkflowExecutionEngine()
    
    # Create a sample irrigation workflow
    workflow = AgriculturalWorkflow(
        workflow_id=f"wf-{uuid.uuid4().hex[:8]}",
        name="Field A Irrigation Schedule",
        description="Automated irrigation scheduling based on soil moisture, weather forecast, and crop water needs",
        metadata={
            "priority": "high",
            "requestedBy": "Field Manager",
            "fieldCount": 1,
            "cropType": "Corn",
            "fieldSize": "75 acres"
        }
    )
    
    # Add steps to the workflow
    workflow.add_step(WorkflowStep(
        step_id="step-1",
        name="Collect Sensor Data",
        agent="sensor-data-agent",
        description="Gather data from soil moisture sensors across all fields",
        parameters={"sensorIds": ["SM001", "SM002", "SM003"], "depth": "12in"}
    ))
    
    workflow.add_step(WorkflowStep(
        step_id="step-2",
        name="Fetch Weather Forecast",
        agent="weather-agent",
        description="Retrieve 7-day weather forecast data from meteorological APIs",
        parameters={"location": "41.8781,-87.6298", "days": 7}
    ))
    
    workflow.add_step(WorkflowStep(
        step_id="step-3",
        name="Calculate Crop Water Requirements",
        agent="crop-analysis-agent",
        description="Determine water requirements based on crop type and growth stage",
        parameters={"cropType": "corn", "growthStage": "V6", "fieldId": "F-A-23"}
    ))
    
    workflow.add_step(WorkflowStep(
        step_id="step-4",
        name="Generate Irrigation Schedule",
        agent="schedule-optimizer-agent",
        description="Create an optimized irrigation schedule for each field",
        parameters={"optimizationTarget": "waterEfficiency", "maxDuration": "16h"}
    ))
    
    workflow.add_step(WorkflowStep(
        step_id="step-5",
        name="Send Commands to Irrigation System",
        agent="irrigation-control-agent",
        description="Transmit schedule to automated irrigation controllers",
        parameters={"controllerId": "IC-F-A-1", "mode": "automated"}
    ))
    
    # Register and execute the workflow
    engine.register_workflow(workflow)
    asyncio.create_task(engine.execute_workflow(workflow.id))
    
    # Monitor workflow progress
    while True:
        await asyncio.sleep(1)
        workflow_data = engine.get_workflow(workflow.id).to_dict()
        print(f"\nWorkflow: {workflow_data['name']} (Status: {workflow_data['status']})")
        print(f"Progress: {workflow_data['progress'] * 100:.0f}%")
        
        # Print step statuses
        for step in workflow_data['steps']:
            status_icon = {
                "pending": "⏳",
                "in-progress": "🔄",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(step['status'], "?")
            print(f"{status_icon} {step['name']} - {step['status']}")
        
        # Break the loop when workflow is done
        if workflow_data['status'] in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            print("\nWorkflow execution finished!")
            print(f"Final status: {workflow_data['status']}")
            
            # Print execution summary
            if workflow_data['startTime'] and workflow_data['endTime']:
                print(f"Started: {workflow_data['startTime']}")
                print(f"Ended: {workflow_data['endTime']}")
                print(f"Total duration: {workflow_data['totalDuration'] / 1000:.1f} seconds")
            
            # Print step outputs
            print("\nStep Outputs:")
            for step in workflow_data['steps']:
                print(f"\n--- {step['name']} ({step['status']}) ---")
                if step['output']:
                    print(f"Output: {step['output']}")
                if step['error']:
                    print(f"Error: {step['error']}")
            
            break


if __name__ == "__main__":
    asyncio.run(create_and_run_sample_workflow())
