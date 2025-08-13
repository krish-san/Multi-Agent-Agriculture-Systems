
from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
import uuid


class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    COMMAND = "command"
    RESPONSE = "response"
    STATUS = "status"
    DATA = "data"
    ERROR = "error"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentCapability(str, Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    COORDINATION = "coordination"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    TEXT_PROCESSING = "text_processing"
    API_INTERACTION = "api_interaction"
    PLANNING = "planning"
    EXECUTION = "execution"


class AgentState(BaseModel):
    
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    agent_type: str = "worker"
    status: AgentStatus = AgentStatus.AVAILABLE
    capabilities: List[AgentCapability] = Field(default_factory=list)
    current_task_id: Optional[str] = None
    
    # Performance metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_execution_time: float = 0.0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Configuration
    max_concurrent_tasks: int = 1
    timeout_seconds: int = 300
    
    # Health information
    health_check_passed: bool = True
    error_message: Optional[str] = None
    
    # Context and state data
    context: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('agent_id')
    def validate_agent_id(cls, v):
        if not v:
            return str(uuid.uuid4())
        return v
    
    def update_performance(self, execution_time: float = 0.0, success: bool = True):
        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1
        
        # Update average execution time
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            self.average_execution_time = (
                (self.average_execution_time * (total_tasks - 1) + execution_time) / total_tasks
            )
        
        self.last_activity = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    @property
    def success_rate(self) -> float:
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks == 0:
            return 1.0
        return self.tasks_completed / total_tasks
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Message(BaseModel):
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    receiver_id: str
    message_type: MessageType
    content: Dict[str, Any]
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Delivery tracking
    delivered: bool = False
    processed: bool = False
    response_to: Optional[str] = None  # ID of message this is responding to
    
    # Timeout and retry
    expires_at: Optional[datetime] = None
    max_retries: int = 3
    retry_count: int = 0
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Task(BaseModel):
    
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    task_type: str = "general"
    status: TaskStatus = TaskStatus.PENDING
    
    # Assignment
    assigned_agent_id: Optional[str] = None
    required_capabilities: List[AgentCapability] = Field(default_factory=list)
    
    # Parameters and context
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # Task IDs
    blocks: List[str] = Field(default_factory=list)      # Task IDs this blocks
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results and error handling
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Priority and constraints
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_count: int = 0
    
    def assign_task(self, agent_id: str):
        self.status = TaskStatus.IN_PROGRESS
        self.assigned_agent_id = agent_id
        self.started_at = datetime.utcnow()
    
    def start_task(self, agent_id: str):
        self.status = TaskStatus.IN_PROGRESS
        self.assigned_agent_id = agent_id
        self.started_at = datetime.utcnow()
    
    def complete_task(self, result: Dict[str, Any]):
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.utcnow()
    
    def fail_task(self, error_message: str):
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowStep(BaseModel):
    step_id: str
    name: str
    agent_type: Optional[str] = None  # Type of agent required
    task_template: Dict[str, Any] = Field(default_factory=dict)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    next_steps: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "forbid"


class WorkflowState(BaseModel):
    
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    
    # Workflow definition
    steps: Dict[str, WorkflowStep] = Field(default_factory=dict)
    entry_point: str
    
    # Execution state
    current_step: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    failed_steps: List[str] = Field(default_factory=list)
    
    # Context and shared data
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Status
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"
    
    # Active tasks
    active_tasks: Dict[str, str] = Field(default_factory=dict)  # step_id -> task_id
    
    def start_workflow(self):
        self.status = "running"
        self.started_at = datetime.utcnow()
        self.current_step = self.entry_point
    
    def complete_step(self, step_id: str, result: Dict[str, Any]):
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
        
        # Add to execution history
        self.execution_history.append({
            "step_id": step_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed",
            "result": result
        })
        
        # Remove from active tasks
        if step_id in self.active_tasks:
            del self.active_tasks[step_id]
    
    def fail_step(self, step_id: str, error: str):
        if step_id not in self.failed_steps:
            self.failed_steps.append(step_id)
        
        # Add to execution history
        self.execution_history.append({
            "step_id": step_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "error": error
        })
        
        # Remove from active tasks
        if step_id in self.active_tasks:
            del self.active_tasks[step_id]
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemState(BaseModel):
    
    # Collections of system entities
    agents: Dict[str, AgentState] = Field(default_factory=dict)
    workflows: Dict[str, WorkflowState] = Field(default_factory=dict)
    tasks: Dict[str, Task] = Field(default_factory=dict)
    messages: Dict[str, Message] = Field(default_factory=dict)
    
    # System metadata
    system_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # System health
    total_agents: int = 0
    active_agents: int = 0
    total_workflows: int = 0
    active_workflows: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    
    def update_metrics(self):
        self.total_agents = len(self.agents)
        self.active_agents = len([a for a in self.agents.values() if a.status not in [AgentStatus.OFFLINE, AgentStatus.ERROR]])
        
        self.total_workflows = len(self.workflows)
        self.active_workflows = len([w for w in self.workflows.values() if w.status == "running"])
        
        self.total_tasks = len(self.tasks)
        self.completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        
        self.last_updated = datetime.utcnow()
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
