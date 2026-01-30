"""
CrewAI tools for ClaudeForge agents.
File operations, Git commands, test runners, and spec management.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from crewai.tools import tool

PROJECTS_PATH = os.getenv("PROJECTS_PATH", "/projects")


@tool("Read File")
def read_file(file_path: str) -> str:
    """
    Read contents of a file.

    Args:
        file_path: Path to the file relative to project root or absolute path.

    Returns:
        File contents as string, or error message.
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / file_path

        if not path.exists():
            return f"Error: File not found: {file_path}"

        if not path.is_file():
            return f"Error: Not a file: {file_path}"

        with open(path) as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@tool("Write File")
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file, creating directories if needed.

    Args:
        file_path: Path to the file relative to project root or absolute path.
        content: Content to write to the file.

    Returns:
        Success message or error.
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / file_path

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(content)

        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool("Edit File")
def edit_file(file_path: str, old_text: str, new_text: str) -> str:
    """
    Edit a file by replacing old_text with new_text.

    Args:
        file_path: Path to the file.
        old_text: Text to find and replace.
        new_text: Replacement text.

    Returns:
        Success message or error.
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / file_path

        if not path.exists():
            return f"Error: File not found: {file_path}"

        with open(path) as f:
            content = f.read()

        if old_text not in content:
            return f"Error: Text not found in {file_path}"

        new_content = content.replace(old_text, new_text, 1)

        with open(path, "w") as f:
            f.write(new_content)

        return f"Successfully edited {file_path}"
    except Exception as e:
        return f"Error editing file: {e}"


@tool("List Directory")
def list_directory(dir_path: str) -> str:
    """
    List contents of a directory.

    Args:
        dir_path: Path to the directory.

    Returns:
        Formatted directory listing or error.
    """
    try:
        path = Path(dir_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / dir_path

        if not path.exists():
            return f"Error: Directory not found: {dir_path}"

        if not path.is_dir():
            return f"Error: Not a directory: {dir_path}"

        items = []
        for item in sorted(path.iterdir()):
            prefix = "[DIR] " if item.is_dir() else "[FILE]"
            items.append(f"{prefix} {item.name}")

        return "\n".join(items) if items else "(empty directory)"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool("Git Status")
def git_status(project_path: str) -> str:
    """
    Get git status for a project.

    Args:
        project_path: Path to the project directory.

    Returns:
        Git status output or error.
    """
    try:
        path = Path(project_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / project_path

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return f"Git error: {result.stderr}"

        return result.stdout if result.stdout else "Working tree clean"
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except Exception as e:
        return f"Error running git status: {e}"


@tool("Git Commit")
def git_commit(project_path: str, message: str, files: Optional[str] = None) -> str:
    """
    Stage and commit changes to git.

    Args:
        project_path: Path to the project directory.
        message: Commit message.
        files: Optional space-separated list of files to stage. If not provided, stages all changes.

    Returns:
        Commit result or error.
    """
    try:
        path = Path(project_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / project_path

        # Stage files
        if files:
            file_list = files.split()
            subprocess.run(
                ["git", "add"] + file_list,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30,
            )
        else:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=30,
            )

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return "Nothing to commit"
            return f"Git commit error: {result.stderr}"

        return f"Committed: {message}"
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except Exception as e:
        return f"Error running git commit: {e}"


@tool("Git Diff")
def git_diff(project_path: str, file_path: Optional[str] = None) -> str:
    """
    Get git diff for changes.

    Args:
        project_path: Path to the project directory.
        file_path: Optional specific file to diff.

    Returns:
        Diff output or error.
    """
    try:
        path = Path(project_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / project_path

        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path)

        result = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        return result.stdout if result.stdout else "No changes"
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except Exception as e:
        return f"Error running git diff: {e}"


@tool("Run Tests")
def run_tests(project_path: str, test_command: Optional[str] = None) -> str:
    """
    Run tests for a project.

    Args:
        project_path: Path to the project directory.
        test_command: Optional custom test command. Defaults to auto-detection.

    Returns:
        Test output or error.
    """
    try:
        path = Path(project_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / project_path

        # Auto-detect test framework if not specified
        if not test_command:
            if (path / "pytest.ini").exists() or (path / "pyproject.toml").exists():
                test_command = "pytest -v"
            elif (path / "package.json").exists():
                test_command = "npm test"
            elif (path / "Makefile").exists():
                test_command = "make test"
            else:
                return "Error: Could not detect test framework"

        result = subprocess.run(
            test_command.split(),
            cwd=path,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for tests
        )

        output = result.stdout + result.stderr
        status = "PASSED" if result.returncode == 0 else "FAILED"

        return f"Tests {status}:\n{output}"
    except subprocess.TimeoutExpired:
        return "Error: Tests timed out after 5 minutes"
    except Exception as e:
        return f"Error running tests: {e}"


@tool("Search Files")
def search_files(project_path: str, pattern: str, file_pattern: str = "*") -> str:
    """
    Search for text pattern in project files.

    Args:
        project_path: Path to the project directory.
        pattern: Text pattern to search for.
        file_pattern: Glob pattern for files to search (default: all files).

    Returns:
        Search results or error.
    """
    try:
        path = Path(project_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / project_path

        results = []
        for file_path in path.rglob(file_pattern):
            if file_path.is_file() and not any(
                part.startswith(".") for part in file_path.parts
            ):
                try:
                    with open(file_path) as f:
                        for i, line in enumerate(f, 1):
                            if pattern in line:
                                rel_path = file_path.relative_to(path)
                                results.append(f"{rel_path}:{i}: {line.strip()}")
                except (UnicodeDecodeError, PermissionError):
                    continue

        return "\n".join(results[:50]) if results else f"No matches found for '{pattern}'"
    except Exception as e:
        return f"Error searching files: {e}"


@tool("Create Directory")
def create_directory(dir_path: str) -> str:
    """
    Create a directory and any necessary parent directories.

    Args:
        dir_path: Path to the directory to create.

    Returns:
        Success message or error.
    """
    try:
        path = Path(dir_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / dir_path

        path.mkdir(parents=True, exist_ok=True)
        return f"Created directory: {dir_path}"
    except Exception as e:
        return f"Error creating directory: {e}"


@tool("Delete File")
def delete_file(file_path: str) -> str:
    """
    Delete a file.

    Args:
        file_path: Path to the file to delete.

    Returns:
        Success message or error.
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / file_path

        if not path.exists():
            return f"Error: File not found: {file_path}"

        if not path.is_file():
            return f"Error: Not a file: {file_path}"

        path.unlink()
        return f"Deleted: {file_path}"
    except Exception as e:
        return f"Error deleting file: {e}"


@tool("Check Docker Standards")
def check_docker_standards(dockerfile_path: str) -> str:
    """
    Validate a Dockerfile against ClaudeForge standards.

    Args:
        dockerfile_path: Path to the Dockerfile.

    Returns:
        Validation results.
    """
    try:
        path = Path(dockerfile_path)
        if not path.is_absolute():
            path = Path(PROJECTS_PATH) / dockerfile_path

        if not path.exists():
            return f"Error: Dockerfile not found: {dockerfile_path}"

        with open(path) as f:
            content = f.read()

        issues = []
        recommendations = []

        # Check for multi-stage build
        if "FROM" in content and content.count("FROM") < 2:
            recommendations.append("Consider using multi-stage build for smaller images")

        # Check for non-root user
        if "USER" not in content:
            issues.append("No non-root USER specified (security risk)")

        # Check for HEALTHCHECK
        if "HEALTHCHECK" not in content:
            recommendations.append("Add HEALTHCHECK for container health monitoring")

        # Check for .dockerignore mention
        if "COPY . ." in content or "ADD . ." in content:
            recommendations.append("Ensure .dockerignore is configured to exclude unnecessary files")

        # Check for pinned versions
        lines = content.split("\n")
        for line in lines:
            if line.startswith("FROM") and ":latest" in line:
                issues.append("Using :latest tag - pin to specific version")

        result = "Docker Standards Check:\n"
        if issues:
            result += "\nISSUES:\n" + "\n".join(f"- {i}" for i in issues)
        if recommendations:
            result += "\nRECOMMENDATIONS:\n" + "\n".join(f"- {r}" for r in recommendations)
        if not issues and not recommendations:
            result += "All checks passed!"

        return result
    except Exception as e:
        return f"Error checking Dockerfile: {e}"
