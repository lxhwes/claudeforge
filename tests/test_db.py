"""
Tests for database operations.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from db import (
    get_db,
    init_db,
    register_project,
    get_project,
    list_projects,
    create_feature,
    get_feature,
    update_feature_status,
    add_log,
    get_logs,
    get_next_feature_number,
)
from models import PhaseStatus, ProjectStatus, WorkflowPhase


class TestDatabase:
    """Test database operations."""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        """Set up fresh database for each test."""
        import db
        db.DATABASE_PATH = str(tmp_path / "test.db")
        init_db()

    def test_register_project(self):
        """Test project registration."""
        project = register_project("test-project", "/projects/test-project")

        assert project.name == "test-project"
        assert project.path == "/projects/test-project"
        assert project.status == ProjectStatus.ACTIVE

    def test_register_project_idempotent(self):
        """Test that registering same project twice returns existing."""
        project1 = register_project("test-project", "/projects/test-project")
        project2 = register_project("test-project", "/projects/test-project")

        assert project1.id == project2.id

    def test_get_project(self):
        """Test retrieving a project."""
        register_project("test-project", "/projects/test-project")
        project = get_project("test-project")

        assert project is not None
        assert project.name == "test-project"

    def test_get_nonexistent_project(self):
        """Test retrieving non-existent project returns None."""
        project = get_project("nonexistent")
        assert project is None

    def test_list_projects(self):
        """Test listing all projects."""
        register_project("project-a", "/projects/a")
        register_project("project-b", "/projects/b")

        projects = list_projects()

        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "project-a" in names
        assert "project-b" in names

    def test_create_feature(self):
        """Test feature creation."""
        project = register_project("test", "/projects/test")
        feature = create_feature("FEAT-20260129-001", project.id, "Test feature")

        assert feature.feature_id == "FEAT-20260129-001"
        assert feature.project_id == project.id
        assert feature.description == "Test feature"
        assert feature.status == PhaseStatus.DRAFT

    def test_get_feature(self):
        """Test retrieving a feature."""
        project = register_project("test", "/projects/test")
        create_feature("FEAT-20260129-001", project.id, "Test feature")

        feature = get_feature("FEAT-20260129-001")

        assert feature is not None
        assert feature.feature_id == "FEAT-20260129-001"

    def test_update_feature_status(self):
        """Test updating feature status."""
        project = register_project("test", "/projects/test")
        create_feature("FEAT-20260129-001", project.id, "Test feature")

        result = update_feature_status(
            "FEAT-20260129-001",
            PhaseStatus.IN_PROGRESS,
            WorkflowPhase.DESIGN,
        )

        assert result is True

        feature = get_feature("FEAT-20260129-001")
        assert feature.status == PhaseStatus.IN_PROGRESS
        assert feature.current_phase == WorkflowPhase.DESIGN

    def test_add_and_get_logs(self):
        """Test adding and retrieving logs."""
        project = register_project("test", "/projects/test")
        create_feature("FEAT-20260129-001", project.id, "Test feature")

        add_log("FEAT-20260129-001", "Test message 1", "info")
        add_log("FEAT-20260129-001", "Test message 2", "error")

        logs = get_logs("FEAT-20260129-001")

        assert len(logs) == 2
        messages = [log.message for log in logs]
        assert "Test message 1" in messages
        assert "Test message 2" in messages

    def test_feature_number_increment(self):
        """Test that feature numbers increment correctly."""
        num1 = get_next_feature_number()
        num2 = get_next_feature_number()
        num3 = get_next_feature_number()

        assert num1 == 1
        assert num2 == 2
        assert num3 == 3
