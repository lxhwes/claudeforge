"""
Tests for FastAPI endpoints.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create test client with fresh database."""
        import db
        import utils

        db.DATABASE_PATH = str(tmp_path / "test.db")
        utils.PROJECTS_PATH = str(tmp_path / "projects")
        (tmp_path / "projects").mkdir()

        db.init_db()

        from main import app
        return TestClient(app)

    def test_health_check(self, client):
        """Test health endpoint returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestProjectEndpoints:
    """Test project-related endpoints."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create test client with sample projects."""
        import db
        import utils

        db.DATABASE_PATH = str(tmp_path / "test.db")
        utils.PROJECTS_PATH = str(tmp_path / "projects")

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "sample-project").mkdir()
        (projects_dir / "another-project").mkdir()

        db.init_db()

        from main import app
        return TestClient(app)

    def test_list_projects(self, client):
        """Test listing projects."""
        response = client.get("/api/projects/list")

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert len(data["projects"]) >= 2

    def test_get_project(self, client):
        """Test getting single project."""
        # First list to register
        client.get("/api/projects/list")

        response = client.get("/api/projects/sample-project")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "sample-project"

    def test_get_nonexistent_project(self, client):
        """Test getting non-existent project."""
        response = client.get("/api/projects/nonexistent")

        assert response.status_code == 404


class TestWorkflowEndpoints:
    """Test workflow-related endpoints."""

    @pytest.fixture
    def client(self, tmp_path):
        """Create test client with sample project."""
        import db
        import utils

        db.DATABASE_PATH = str(tmp_path / "test.db")
        utils.PROJECTS_PATH = str(tmp_path / "projects")

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "sample-project").mkdir()

        db.init_db()
        db.register_project("sample-project", str(projects_dir / "sample-project"))

        from main import app
        return TestClient(app)

    def test_start_workflow(self, client):
        """Test starting a workflow."""
        response = client.post(
            "/api/agents/start",
            json={
                "project": "sample-project",
                "feature_desc": "Add user authentication",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "feat_id" in data
        assert data["feat_id"].startswith("FEAT-")

    def test_get_workflow_status_not_found(self, client):
        """Test getting status for non-existent workflow."""
        response = client.get("/api/agents/status/FEAT-20260129-999")

        assert response.status_code == 404

    def test_list_running_workflows(self, client):
        """Test listing running workflows."""
        response = client.get("/api/agents/running")

        assert response.status_code == 200
        data = response.json()
        assert "running" in data


class TestSpecEndpoints:
    """Test spec-related endpoints."""

    @pytest.fixture
    def client_with_spec(self, tmp_path):
        """Create test client with a spec."""
        import db
        import utils
        from utils import write_phase_spec
        from models import PhaseStatus, WorkflowPhase

        db.DATABASE_PATH = str(tmp_path / "test.db")
        utils.PROJECTS_PATH = str(tmp_path / "projects")

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "sample-project").mkdir()

        db.init_db()
        project = db.register_project("sample-project", str(projects_dir / "sample-project"))
        db.create_feature("FEAT-20260129-001", project.id, "Test feature")

        # Create a spec
        write_phase_spec(
            "sample-project",
            "FEAT-20260129-001",
            WorkflowPhase.REQUIREMENTS,
            "## Requirements\n- Feature A",
            PhaseStatus.PENDING_APPROVAL,
        )

        from main import app
        return TestClient(app)

    def test_get_spec(self, client_with_spec):
        """Test getting spec data."""
        response = client_with_spec.get("/api/specs/sample-project/FEAT-20260129-001")

        assert response.status_code == 200
        data = response.json()
        assert data["feature_id"] == "FEAT-20260129-001"
        assert "phases" in data

    def test_approve_spec(self, client_with_spec):
        """Test approving a spec phase."""
        response = client_with_spec.post(
            "/api/specs/approve",
            json={
                "feat_id": "FEAT-20260129-001",
                "phase": "requirements",
                "action": "approve",
                "comment": "Looks good!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_reject_spec(self, client_with_spec):
        """Test rejecting a spec phase."""
        response = client_with_spec.post(
            "/api/specs/approve",
            json={
                "feat_id": "FEAT-20260129-001",
                "phase": "requirements",
                "action": "reject",
                "comment": "Needs more detail",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSearchEndpoint:
    """Test search functionality."""

    @pytest.fixture
    def client_with_features(self, tmp_path):
        """Create test client with multiple features."""
        import db
        import utils

        db.DATABASE_PATH = str(tmp_path / "test.db")
        utils.PROJECTS_PATH = str(tmp_path / "projects")

        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "project-a").mkdir()

        db.init_db()
        project = db.register_project("project-a", str(projects_dir / "project-a"))
        db.create_feature("FEAT-20260129-001", project.id, "Auth feature")
        db.create_feature("FEAT-20260129-002", project.id, "API feature")

        from main import app
        return TestClient(app)

    def test_search_specs(self, client_with_features):
        """Test searching specs."""
        response = client_with_features.get("/api/search?query=FEAT-20260129")

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
