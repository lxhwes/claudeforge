"""
Pytest configuration and fixtures for ClaudeForge tests.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Set test environment variables
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["PROJECTS_PATH"] = tempfile.mkdtemp()
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"


@pytest.fixture
def temp_projects_dir():
    """Create a temporary projects directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["PROJECTS_PATH"] = tmpdir
        yield Path(tmpdir)


@pytest.fixture
def sample_project(temp_projects_dir):
    """Create a sample project for testing."""
    project_dir = temp_projects_dir / "sample-project"
    project_dir.mkdir(parents=True)

    # Create basic project structure
    (project_dir / "README.md").write_text("# Sample Project")
    (project_dir / "src").mkdir()
    (project_dir / "src" / "main.py").write_text('print("Hello")')

    return project_dir


@pytest.fixture
def temp_db():
    """Create a temporary in-memory database."""
    import db
    db.DATABASE_PATH = ":memory:"
    db.init_db()
    yield
