"""
Pydantic models for ClaudeForge API and data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PhaseStatus(str, Enum):
    """Status states for workflow phases."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class WorkflowPhase(str, Enum):
    """Workflow phase names."""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    TASKS = "tasks"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    REVIEW = "review"


class ProjectStatus(str, Enum):
    """Project status states."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    ERROR = "error"


class Approval(BaseModel):
    """Approval record for a spec phase."""
    user: str = "system"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    comment: str = ""


class SpecPhase(BaseModel):
    """Specification for a single workflow phase."""
    feature_id: str
    phase: WorkflowPhase
    status: PhaseStatus = PhaseStatus.DRAFT
    content: str = ""
    approvals: list[Approval] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Project(BaseModel):
    """Project information."""
    id: Optional[int] = None
    name: str
    path: str
    status: ProjectStatus = ProjectStatus.ACTIVE


class Feature(BaseModel):
    """Feature record."""
    id: Optional[int] = None
    feature_id: str
    project_id: int
    description: str
    status: PhaseStatus = PhaseStatus.DRAFT
    current_phase: WorkflowPhase = WorkflowPhase.REQUIREMENTS
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LogEntry(BaseModel):
    """Log entry for agent activity."""
    id: Optional[int] = None
    feature_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: str
    level: str = "info"


# API Request/Response Models

class StartWorkflowRequest(BaseModel):
    """Request to start a new workflow."""
    project: str
    feature_desc: str


class StartWorkflowResponse(BaseModel):
    """Response from starting a workflow."""
    feat_id: str
    message: str = "Workflow started"


class ApproveSpecRequest(BaseModel):
    """Request to approve or reject a spec phase."""
    feat_id: str
    phase: WorkflowPhase
    action: str  # "approve" or "reject"
    comment: str = ""


class ApproveSpecResponse(BaseModel):
    """Response from approval action."""
    success: bool
    message: str


class AgentStatusResponse(BaseModel):
    """Response with agent workflow status."""
    feat_id: str
    status: PhaseStatus
    current_phase: WorkflowPhase
    progress: float  # 0.0 to 1.0
    logs: list[str] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    """Response with list of projects."""
    projects: list[Project]


class SpecResponse(BaseModel):
    """Response with spec data for all phases."""
    feature_id: str
    project_name: str
    description: str
    phases: dict[str, SpecPhase]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "0.1.0"
    database: str = "connected"


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    message: str
    level: str = "info"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
