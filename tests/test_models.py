"""
Tests for Pydantic models.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from models import (
    Approval,
    SpecPhase,
    Project,
    Feature,
    LogEntry,
    StartWorkflowRequest,
    ApproveSpecRequest,
    PhaseStatus,
    WorkflowPhase,
    ProjectStatus,
)


class TestApprovalModel:
    """Test Approval model."""

    def test_approval_defaults(self):
        """Test approval with default values."""
        approval = Approval()

        assert approval.user == "system"
        assert approval.comment == ""
        assert isinstance(approval.timestamp, datetime)

    def test_approval_with_values(self):
        """Test approval with custom values."""
        now = datetime.utcnow()
        approval = Approval(user="admin", timestamp=now, comment="Approved!")

        assert approval.user == "admin"
        assert approval.timestamp == now
        assert approval.comment == "Approved!"


class TestSpecPhaseModel:
    """Test SpecPhase model."""

    def test_spec_phase_required_fields(self):
        """Test spec phase with required fields."""
        spec = SpecPhase(
            feature_id="FEAT-20260129-001",
            phase=WorkflowPhase.REQUIREMENTS,
        )

        assert spec.feature_id == "FEAT-20260129-001"
        assert spec.phase == WorkflowPhase.REQUIREMENTS
        assert spec.status == PhaseStatus.DRAFT
        assert spec.content == ""
        assert spec.approvals == []

    def test_spec_phase_full(self):
        """Test spec phase with all fields."""
        now = datetime.utcnow()
        spec = SpecPhase(
            feature_id="FEAT-20260129-001",
            phase=WorkflowPhase.DESIGN,
            status=PhaseStatus.APPROVED,
            content="## Design\n- Component A",
            approvals=[Approval(user="reviewer", comment="LGTM")],
            dependencies=["FEAT-20260128-001"],
            created_at=now,
            updated_at=now,
        )

        assert spec.status == PhaseStatus.APPROVED
        assert len(spec.approvals) == 1
        assert spec.dependencies == ["FEAT-20260128-001"]


class TestProjectModel:
    """Test Project model."""

    def test_project_basic(self):
        """Test project with basic fields."""
        project = Project(name="test-project", path="/projects/test")

        assert project.name == "test-project"
        assert project.path == "/projects/test"
        assert project.status == ProjectStatus.ACTIVE
        assert project.id is None

    def test_project_with_id(self):
        """Test project with ID."""
        project = Project(id=1, name="test", path="/test", status=ProjectStatus.ARCHIVED)

        assert project.id == 1
        assert project.status == ProjectStatus.ARCHIVED


class TestFeatureModel:
    """Test Feature model."""

    def test_feature_basic(self):
        """Test feature with basic fields."""
        feature = Feature(
            feature_id="FEAT-20260129-001",
            project_id=1,
            description="Add auth",
        )

        assert feature.feature_id == "FEAT-20260129-001"
        assert feature.project_id == 1
        assert feature.description == "Add auth"
        assert feature.status == PhaseStatus.DRAFT
        assert feature.current_phase == WorkflowPhase.REQUIREMENTS


class TestRequestModels:
    """Test API request models."""

    def test_start_workflow_request(self):
        """Test start workflow request."""
        request = StartWorkflowRequest(
            project="test-project",
            feature_desc="Add user authentication",
        )

        assert request.project == "test-project"
        assert request.feature_desc == "Add user authentication"

    def test_approve_spec_request(self):
        """Test approve spec request."""
        request = ApproveSpecRequest(
            feat_id="FEAT-20260129-001",
            phase=WorkflowPhase.REQUIREMENTS,
            action="approve",
            comment="Looks good!",
        )

        assert request.feat_id == "FEAT-20260129-001"
        assert request.phase == WorkflowPhase.REQUIREMENTS
        assert request.action == "approve"
        assert request.comment == "Looks good!"


class TestEnums:
    """Test enum values."""

    def test_phase_status_values(self):
        """Test PhaseStatus enum values."""
        assert PhaseStatus.DRAFT.value == "draft"
        assert PhaseStatus.PENDING_APPROVAL.value == "pending_approval"
        assert PhaseStatus.APPROVED.value == "approved"
        assert PhaseStatus.REJECTED.value == "rejected"
        assert PhaseStatus.IN_PROGRESS.value == "in_progress"
        assert PhaseStatus.COMPLETED.value == "completed"

    def test_workflow_phase_values(self):
        """Test WorkflowPhase enum values."""
        assert WorkflowPhase.REQUIREMENTS.value == "requirements"
        assert WorkflowPhase.DESIGN.value == "design"
        assert WorkflowPhase.TASKS.value == "tasks"
        assert WorkflowPhase.IMPLEMENTATION.value == "implementation"
        assert WorkflowPhase.VERIFICATION.value == "verification"
        assert WorkflowPhase.REVIEW.value == "review"

    def test_project_status_values(self):
        """Test ProjectStatus enum values."""
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.ARCHIVED.value == "archived"
        assert ProjectStatus.ERROR.value == "error"
