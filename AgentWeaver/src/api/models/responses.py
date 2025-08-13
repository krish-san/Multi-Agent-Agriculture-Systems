
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AgentStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentResponse(BaseModel):
    
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    type: str = Field(..., description="Agent type (e.g., 'text_analysis', 'data_processing')")
    status: AgentStatus = Field(..., description="Current agent status")
    capabilities: List[str] = Field(default_factory=list, description="List of agent capabilities")
    current_task: Optional[str] = Field(None, description="Currently assigned task ID")
    last_activity: Optional[datetime] = Field(None, description="Timestamp of last activity")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Agent performance data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional agent metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "agent_001",
                "name": "Text Analysis Specialist",
                "type": "text_analysis",
                "status": "active",
                "capabilities": ["sentiment_analysis", "entity_extraction"],
                "current_task": "task_123",
                "last_activity": "2025-08-02T14:20:00Z",
                "performance_metrics": {
                    "tasks_completed": 15,
                    "avg_processing_time": 2.3,
                    "success_rate": 0.95
                },
                "metadata": {
                    "version": "1.0",
                    "specialized_domain": "customer_feedback"
                }
            }
        }


class AgentListResponse(BaseModel):
    
    agents: List[AgentResponse] = Field(..., description="List of agents")
    total_count: int = Field(..., description="Total number of agents")
    active_count: int = Field(..., description="Number of active agents")
    busy_count: int = Field(..., description="Number of busy agents")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional listing metadata")

    class Config:
        schema_extra = {
            "example": {
                "agents": [
                    {
                        "id": "agent_001",
                        "name": "Text Analyzer",
                        "type": "text_analysis",
                        "status": "active",
                        "capabilities": ["sentiment_analysis"],
                        "current_task": None,
                        "last_activity": "2025-08-02T14:20:00Z",
                        "performance_metrics": {"tasks_completed": 15},
                        "metadata": {}
                    }
                ],
                "total_count": 1,
                "active_count": 1,
                "busy_count": 0,
                "metadata": {"last_updated": "2025-08-02T14:20:00Z"}
            }
        }


class WorkflowResponse(BaseModel):
    
    id: str = Field(..., description="Unique workflow identifier")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    created_at: datetime = Field(..., description="Workflow creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Workflow start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion timestamp")
    current_step: Optional[str] = Field(None, description="Current execution step")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Workflow progress (0.0 to 1.0)")
    assigned_agents: List[str] = Field(default_factory=list, description="List of assigned agent IDs")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow input data")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Workflow output data")
    error_message: Optional[str] = Field(None, description="Error message if workflow failed")
    execution_time: Optional[float] = Field(None, description="Total execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "workflow_001",
                "status": "running",
                "created_at": "2025-08-02T14:15:00Z",
                "started_at": "2025-08-02T14:15:05Z",
                "completed_at": None,
                "current_step": "text_analysis",
                "progress": 0.6,
                "assigned_agents": ["agent_001", "agent_002"],
                "input_data": {
                    "text": "Sample text to analyze",
                    "metadata": {"source": "customer_feedback"}
                },
                "output_data": None,
                "error_message": None,
                "execution_time": None,
                "metadata": {"priority": "high"}
            }
        }


class WorkflowListResponse(BaseModel):
    
    workflows: List[WorkflowResponse] = Field(..., description="List of workflows")
    total_count: int = Field(..., description="Total number of workflows")
    running_count: int = Field(..., description="Number of running workflows")
    completed_count: int = Field(..., description="Number of completed workflows")
    failed_count: int = Field(..., description="Number of failed workflows")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional listing metadata")

    class Config:
        schema_extra = {
            "example": {
                "workflows": [
                    {
                        "id": "workflow_001",
                        "status": "completed",
                        "created_at": "2025-08-02T14:10:00Z",
                        "started_at": "2025-08-02T14:10:05Z",
                        "completed_at": "2025-08-02T14:12:30Z",
                        "current_step": "completed",
                        "progress": 1.0,
                        "assigned_agents": ["agent_001"],
                        "input_data": {"text": "Test input"},
                        "output_data": {"result": "Analysis complete"},
                        "error_message": None,
                        "execution_time": 145.5,
                        "metadata": {}
                    }
                ],
                "total_count": 1,
                "running_count": 0,
                "completed_count": 1,
                "failed_count": 0,
                "metadata": {"last_updated": "2025-08-02T14:20:00Z"}
            }
        }


class SystemStatusResponse(BaseModel):
    
    status: str = Field(..., description="Overall system status")
    uptime: float = Field(..., description="System uptime in seconds")
    version: str = Field(..., description="System version")
    timestamp: datetime = Field(..., description="Status timestamp")
    services: Dict[str, str] = Field(..., description="Service statuses")
    metrics: Dict[str, Union[int, float]] = Field(..., description="System metrics")
    resource_usage: Dict[str, float] = Field(default_factory=dict, description="Resource usage information")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "healthy",
                "uptime": 3600.5,
                "version": "1.0.0",
                "timestamp": "2025-08-02T14:20:00Z",
                "services": {
                    "redis": "connected",
                    "supervisor": "initialized",
                    "websocket_manager": "initialized"
                },
                "metrics": {
                    "active_agents": 5,
                    "running_workflows": 2,
                    "total_workflows_processed": 150,
                    "active_websocket_connections": 3
                },
                "resource_usage": {
                    "memory_percent": 45.2,
                    "cpu_percent": 23.1
                }
            }
        }


class ErrorResponse(BaseModel):
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data provided",
                "details": {
                    "field": "agent_id",
                    "issue": "Required field missing"
                },
                "timestamp": "2025-08-02T14:20:00Z",
                "request_id": "req_123456"
            }
        }
