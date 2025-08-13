
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class WorkflowPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class WorkflowCreateRequest(BaseModel):
    
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow")
    workflow_type: Optional[str] = Field("conditional", description="Type of workflow to execute")
    priority: WorkflowPriority = Field(WorkflowPriority.MEDIUM, description="Workflow execution priority")
    timeout: Optional[int] = Field(300, ge=1, le=3600, description="Workflow timeout in seconds (1-3600)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow metadata")
    agent_preferences: Optional[List[str]] = Field(None, description="Preferred agent IDs for execution")
    callback_url: Optional[str] = Field(None, description="URL to POST results when workflow completes")
    
    @validator('input_data')
    def validate_input_data(cls, v):
        if not v:
            raise ValueError("input_data cannot be empty")
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v and not isinstance(v, dict):
            raise ValueError("metadata must be a dictionary")
        return v

    class Config:
        schema_extra = {
            "example": {
                "input_data": {
                    "text": "This is a sample text for analysis and processing.",
                    "source": "customer_feedback",
                    "language": "en"
                },
                "workflow_type": "conditional",
                "priority": "medium",
                "timeout": 300,
                "metadata": {
                    "user_id": "user_123",
                    "session_id": "session_456",
                    "source_system": "feedback_portal"
                },
                "agent_preferences": ["agent_text_001", "agent_data_002"],
                "callback_url": "https://api.example.com/workflow/callback"
            }
        }


class WorkflowControlRequest(BaseModel):
    
    action: str = Field(..., description="Control action (pause, resume, cancel, restart)")
    reason: Optional[str] = Field(None, description="Reason for the control action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional control metadata")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = {'pause', 'resume', 'cancel', 'restart'}
        if v.lower() not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "action": "pause",
                "reason": "System maintenance required",
                "metadata": {
                    "requested_by": "admin_user",
                    "maintenance_window": "2025-08-02T15:00:00Z"
                }
            }
        }


class AgentRegistrationRequest(BaseModel):
    
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable agent name")
    type: str = Field(..., description="Agent type identifier")
    capabilities: List[str] = Field(..., description="List of agent capabilities")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional agent metadata")
    tags: List[str] = Field(default_factory=list, description="Agent tags for categorization")
    
    @validator('capabilities')
    def validate_capabilities(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Agent must have at least one capability")
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Agent name cannot be empty or whitespace only")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "name": "Advanced Text Analyzer",
                "type": "text_analysis",
                "capabilities": [
                    "sentiment_analysis",
                    "entity_extraction",
                    "language_detection",
                    "topic_classification"
                ],
                "configuration": {
                    "model_version": "v2.1",
                    "confidence_threshold": 0.85,
                    "max_text_length": 10000
                },
                "metadata": {
                    "version": "1.2.0",
                    "specialized_domain": "customer_feedback",
                    "training_date": "2025-07-15"
                },
                "tags": ["nlp", "production", "high-accuracy"]
            }
        }


class AgentUpdateRequest(BaseModel):
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated agent name")
    capabilities: Optional[List[str]] = Field(None, description="Updated capabilities list")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Updated configuration parameters")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    status: Optional[str] = Field(None, description="Updated agent status")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Agent name cannot be empty or whitespace only")
        return v.strip() if v else v
    
    @validator('capabilities')
    def validate_capabilities(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("Capabilities list cannot be empty if provided")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Enhanced Text Analyzer",
                "capabilities": [
                    "sentiment_analysis",
                    "entity_extraction",
                    "language_detection",
                    "topic_classification",
                    "emotion_detection"
                ],
                "configuration": {
                    "model_version": "v2.2",
                    "confidence_threshold": 0.90
                },
                "metadata": {
                    "last_updated": "2025-08-02T14:20:00Z",
                    "performance_improvement": "15%"
                },
                "tags": ["nlp", "production", "enhanced"],
                "status": "active"
            }
        }


class WebSocketConnectionRequest(BaseModel):
    
    client_id: Optional[str] = Field(None, description="Unique client identifier")
    subscription_filters: List[str] = Field(default_factory=list, description="Event filters for subscription")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Client connection metadata")
    
    @validator('subscription_filters')
    def validate_filters(cls, v):
        allowed_filters = {
            'agent_updates', 'workflow_updates', 'system_notifications',
            'error_events', 'performance_metrics', 'all'
        }
        for filter_name in v:
            if filter_name not in allowed_filters:
                raise ValueError(f"Invalid filter: {filter_name}. Allowed: {', '.join(allowed_filters)}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "client_id": "dashboard_client_001",
                "subscription_filters": [
                    "agent_updates",
                    "workflow_updates",
                    "system_notifications"
                ],
                "metadata": {
                    "client_type": "web_dashboard",
                    "user_id": "admin_001",
                    "session_id": "session_789"
                }
            }
        }


class BulkOperationRequest(BaseModel):
    
    operation: str = Field(..., description="Bulk operation type")
    entity_ids: List[str] = Field(..., description="List of entity IDs to operate on")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    async_execution: bool = Field(False, description="Whether to execute asynchronously")
    
    @validator('entity_ids')
    def validate_entity_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one entity ID is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 entity IDs allowed per bulk operation")
        return v
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = {
            'start', 'stop', 'restart', 'delete', 'update_status', 'bulk_update'
        }
        if v.lower() not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "operation": "update_status",
                "entity_ids": ["agent_001", "agent_002", "agent_003"],
                "parameters": {
                    "new_status": "maintenance",
                    "reason": "Scheduled maintenance"
                },
                "async_execution": True
            }
        }
