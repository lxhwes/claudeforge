"""
Tests for utility functions.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from utils import (
    generate_feat_id,
    validate_feature_id,
    get_spec_dir,
    ensure_spec_dir,
    write_phase_spec,
    read_phase_spec,
    scan_projects,
    calculate_progress,
)
from models import PhaseStatus, WorkflowPhase


class TestFeatureId:
    """Test feature ID generation and validation."""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        """Set up fresh database for each test."""
        import db
        db.DATABASE_PATH = str(tmp_path / "test.db")
        db.init_db()

    def test_generate_feat_id_format(self):
        """Test that generated IDs have correct format."""
        feat_id = generate_feat_id()

        assert feat_id.startswith("FEAT-")
        assert len(feat_id) == 17  # FEAT-YYYYMMDD-NNN

    def test_generate_feat_id_unique(self):
        """Test that generated IDs are unique."""
        ids = [generate_feat_id() for _ in range(10)]
        assert len(set(ids)) == 10

    def test_validate_feature_id_valid(self):
        """Test validation of valid feature IDs."""
        assert validate_feature_id("FEAT-20260129-001") is True
        assert validate_feature_id("FEAT-20260129-999") is True

    def test_validate_feature_id_invalid(self):
        """Test validation of invalid feature IDs."""
        assert validate_feature_id("INVALID") is False
        assert validate_feature_id("FEAT-2026-001") is False
        assert validate_feature_id("FEAT-20260129-1") is False
        assert validate_feature_id("") is False


class TestSpecOperations:
    """Test spec file operations."""

    @pytest.fixture
    def temp_projects(self, tmp_path):
        """Set up temporary projects directory."""
        import utils
        utils.PROJECTS_PATH = str(tmp_path)
        return tmp_path

    def test_get_spec_dir(self, temp_projects):
        """Test spec directory path generation."""
        spec_dir = get_spec_dir("test-project", "FEAT-20260129-001")

        expected = temp_projects / "test-project" / ".spec-workflow" / "specs" / "FEAT-20260129-001"
        assert spec_dir == expected

    def test_ensure_spec_dir_creates(self, temp_projects):
        """Test that ensure_spec_dir creates directory."""
        spec_dir = ensure_spec_dir("test-project", "FEAT-20260129-001")

        assert spec_dir.exists()
        assert spec_dir.is_dir()

    def test_write_and_read_phase_spec(self, temp_projects):
        """Test writing and reading phase specs."""
        spec = write_phase_spec(
            "test-project",
            "FEAT-20260129-001",
            WorkflowPhase.REQUIREMENTS,
            "## Requirements\n- Feature A",
            PhaseStatus.DRAFT,
        )

        assert spec.feature_id == "FEAT-20260129-001"
        assert spec.phase == WorkflowPhase.REQUIREMENTS
        assert "Feature A" in spec.content

        # Read it back
        read_spec = read_phase_spec(
            "test-project",
            "FEAT-20260129-001",
            WorkflowPhase.REQUIREMENTS,
        )

        assert read_spec is not None
        assert read_spec.feature_id == spec.feature_id
        assert read_spec.content == spec.content

    def test_read_nonexistent_spec(self, temp_projects):
        """Test reading non-existent spec returns None."""
        spec = read_phase_spec(
            "nonexistent",
            "FEAT-20260129-001",
            WorkflowPhase.REQUIREMENTS,
        )

        assert spec is None


class TestProjectScanning:
    """Test project scanning functionality."""

    @pytest.fixture
    def temp_projects(self, tmp_path):
        """Set up temporary projects directory with sample projects."""
        import utils
        utils.PROJECTS_PATH = str(tmp_path)

        # Create some sample project directories
        (tmp_path / "project-a").mkdir()
        (tmp_path / "project-b").mkdir()
        (tmp_path / ".hidden").mkdir()  # Should be ignored

        return tmp_path

    def test_scan_projects(self, temp_projects):
        """Test scanning for projects."""
        projects = scan_projects()

        assert len(projects) == 2
        assert "project-a" in projects
        assert "project-b" in projects
        assert ".hidden" not in projects

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning empty directory."""
        import utils
        utils.PROJECTS_PATH = str(tmp_path)

        projects = scan_projects()
        assert projects == []
