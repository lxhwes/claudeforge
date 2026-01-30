"""
Tests for CrewAI tools.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


class TestFileTools:
    """Test file operation tools."""

    @pytest.fixture
    def temp_projects(self, tmp_path):
        """Set up temporary projects directory."""
        import tools
        tools.PROJECTS_PATH = str(tmp_path)

        # Create sample file
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / "test.txt").write_text("Hello, World!")

        return tmp_path

    def test_read_file(self, temp_projects):
        """Test reading a file."""
        from tools import read_file

        result = read_file.run("test-project/test.txt")

        assert "Hello, World!" in result

    def test_read_nonexistent_file(self, temp_projects):
        """Test reading non-existent file."""
        from tools import read_file

        result = read_file.run("test-project/nonexistent.txt")

        assert "Error" in result

    def test_write_file(self, temp_projects):
        """Test writing a file."""
        from tools import write_file

        result = write_file.run("test-project/new.txt", "New content")

        assert "Successfully" in result

        # Verify file was created
        assert (temp_projects / "test-project" / "new.txt").exists()
        assert (temp_projects / "test-project" / "new.txt").read_text() == "New content"

    def test_edit_file(self, temp_projects):
        """Test editing a file."""
        from tools import edit_file

        result = edit_file.run("test-project/test.txt", "Hello", "Hi")

        assert "Successfully" in result

        # Verify file was edited
        content = (temp_projects / "test-project" / "test.txt").read_text()
        assert "Hi, World!" in content

    def test_edit_file_text_not_found(self, temp_projects):
        """Test editing file when text not found."""
        from tools import edit_file

        result = edit_file.run("test-project/test.txt", "NotFound", "Replacement")

        assert "Error" in result

    def test_list_directory(self, temp_projects):
        """Test listing directory contents."""
        from tools import list_directory

        # Create some files
        (temp_projects / "test-project" / "subdir").mkdir()
        (temp_projects / "test-project" / "another.txt").write_text("test")

        result = list_directory.run("test-project")

        assert "[DIR]" in result
        assert "[FILE]" in result
        assert "subdir" in result
        assert "test.txt" in result

    def test_create_directory(self, temp_projects):
        """Test creating a directory."""
        from tools import create_directory

        result = create_directory.run("test-project/newdir/nested")

        assert "Created" in result
        assert (temp_projects / "test-project" / "newdir" / "nested").exists()

    def test_search_files(self, temp_projects):
        """Test searching files for pattern."""
        from tools import search_files

        # Create file with searchable content
        (temp_projects / "test-project" / "code.py").write_text("def hello():\n    return 'world'")

        result = search_files.run("test-project", "hello")

        assert "code.py" in result
        assert "hello" in result


class TestDockerTools:
    """Test Docker validation tools."""

    @pytest.fixture
    def temp_projects(self, tmp_path):
        """Set up temporary projects directory."""
        import tools
        tools.PROJECTS_PATH = str(tmp_path)

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        return project_dir

    def test_check_docker_standards_good(self, temp_projects):
        """Test checking a good Dockerfile."""
        from tools import check_docker_standards

        dockerfile = """
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /app /app
RUN useradd -m appuser
USER appuser
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "app.py"]
"""
        (temp_projects / "Dockerfile").write_text(dockerfile)

        result = check_docker_standards.run("test-project/Dockerfile")

        assert "All checks passed" in result or "RECOMMENDATIONS" in result

    def test_check_docker_standards_issues(self, temp_projects):
        """Test checking a Dockerfile with issues."""
        from tools import check_docker_standards

        dockerfile = """
FROM python:latest
COPY . .
CMD ["python", "app.py"]
"""
        (temp_projects / "Dockerfile").write_text(dockerfile)

        result = check_docker_standards.run("test-project/Dockerfile")

        assert "ISSUES" in result or "RECOMMENDATIONS" in result
        # Should flag :latest tag
        assert "latest" in result.lower() or "user" in result.lower()
