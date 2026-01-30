"""
CrewAI agent definitions for ClaudeForge workflow.
Implements the six-phase spec-driven development workflow.
"""

import asyncio
import os
from queue import Queue
from threading import Thread
from typing import Callable, Optional

from crewai import Agent, Crew, Process, Task

from db import add_log, get_feature, get_project_by_id, update_feature_status
from models import PhaseStatus, WorkflowPhase
from tools import (
    check_docker_standards,
    create_directory,
    edit_file,
    git_commit,
    git_diff,
    git_status,
    list_directory,
    read_file,
    run_tests,
    search_files,
    write_file,
)
from utils import backup_spec, update_phase_status, write_phase_spec

# Environment configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_OPUS = os.getenv("CLAUDE_MODEL_OPUS", "claude-3-opus-20240229")
MODEL_SONNET = os.getenv("CLAUDE_MODEL_SONNET", "claude-3-5-sonnet-20241022")
MODEL_HAIKU = os.getenv("CLAUDE_MODEL_HAIKU", "claude-3-haiku-20240307")

# Log queues for WebSocket streaming
log_queues: dict[str, Queue] = {}


def get_log_queue(feat_id: str) -> Queue:
    """Get or create a log queue for a feature."""
    if feat_id not in log_queues:
        log_queues[feat_id] = Queue()
    return log_queues[feat_id]


def log_message(feat_id: str, message: str, level: str = "info") -> None:
    """Log a message to both database and queue."""
    add_log(feat_id, message, level)
    queue = get_log_queue(feat_id)
    queue.put({"message": message, "level": level})


def create_orchestrator() -> Agent:
    """Create the orchestrator agent (Claude Opus)."""
    return Agent(
        role="Workflow Orchestrator",
        goal="Coordinate the spec-driven development workflow, manage phase transitions, and ensure quality gates",
        backstory="""You are the lead coordinator for a spec-driven development workflow.
        Your responsibility is to manage the flow between phases: Requirements → Design → Tasks → Implementation → Verification → Review.
        You ensure each phase produces quality specifications before allowing progression.
        You delegate to specialized agents and aggregate their outputs.""",
        llm=f"anthropic/{MODEL_OPUS}",
        verbose=True,
        allow_delegation=True,
        tools=[read_file, write_file, list_directory],
    )


def create_requirements_analyst() -> Agent:
    """Create the requirements analyst agent (Claude Sonnet)."""
    return Agent(
        role="Requirements Analyst",
        goal="Gather, clarify, and document comprehensive requirements from feature descriptions",
        backstory="""You are an expert requirements analyst with deep experience in software specifications.
        You take vague feature requests and transform them into clear, actionable requirements.
        You ask clarifying questions and ensure completeness of requirements documentation.""",
        llm=f"anthropic/{MODEL_SONNET}",
        verbose=True,
        tools=[read_file, search_files, list_directory],
    )


def create_architect() -> Agent:
    """Create the architect agent (Claude Sonnet)."""
    return Agent(
        role="Software Architect",
        goal="Design robust, scalable architectures based on requirements",
        backstory="""You are a seasoned software architect who creates elegant solutions.
        You analyze requirements and propose architectures with clear component diagrams,
        data flows, and integration patterns. You consider existing codebase patterns.""",
        llm=f"anthropic/{MODEL_SONNET}",
        verbose=True,
        tools=[read_file, search_files, list_directory, check_docker_standards],
    )


def create_task_planner() -> Agent:
    """Create the task planner agent (Claude Sonnet)."""
    return Agent(
        role="Task Planner",
        goal="Break down designs into actionable, well-defined development tasks",
        backstory="""You are an expert at decomposing complex designs into manageable tasks.
        You create clear task definitions with acceptance criteria, dependencies,
        and effort estimates. You ensure tasks are atomic and testable.""",
        llm=f"anthropic/{MODEL_SONNET}",
        verbose=True,
        tools=[read_file, list_directory],
    )


def create_developer() -> Agent:
    """Create the developer agent (Claude Sonnet)."""
    return Agent(
        role="Software Developer",
        goal="Implement features according to task specifications with clean, tested code",
        backstory="""You are an expert software developer who writes clean, maintainable code.
        You follow best practices, write tests, and ensure code quality.
        You commit changes incrementally with clear commit messages.""",
        llm=f"anthropic/{MODEL_SONNET}",
        verbose=True,
        tools=[
            read_file,
            write_file,
            edit_file,
            create_directory,
            git_status,
            git_commit,
            git_diff,
            search_files,
        ],
    )


def create_qa_engineer() -> Agent:
    """Create the QA engineer agent (Claude Sonnet)."""
    return Agent(
        role="QA Engineer",
        goal="Verify implementations through comprehensive testing and quality checks",
        backstory="""You are a meticulous QA engineer who ensures software quality.
        You run tests, verify requirements are met, check for edge cases,
        and report issues with clear reproduction steps.""",
        llm=f"anthropic/{MODEL_SONNET}",
        verbose=True,
        tools=[read_file, run_tests, search_files, list_directory],
    )


def create_reviewer() -> Agent:
    """Create the reviewer agent (Claude Haiku for quick reviews)."""
    return Agent(
        role="Code Reviewer",
        goal="Review implementations for quality, best practices, and improvement opportunities",
        backstory="""You are an experienced code reviewer who provides constructive feedback.
        You check for code quality, potential bugs, security issues, and adherence to standards.
        You suggest improvements while being mindful of scope.""",
        llm=f"anthropic/{MODEL_HAIKU}",
        verbose=True,
        tools=[read_file, search_files, git_diff],
    )


def execute_phase(
    feat_id: str,
    project_name: str,
    phase: WorkflowPhase,
    agent: Agent,
    description: str,
    context_content: str = "",
    auto_approve: bool = False,
) -> str:
    """
    Execute a single workflow phase and persist output to spec file.

    Args:
        feat_id: Feature ID
        project_name: Project name
        phase: Workflow phase to execute
        agent: Agent to run the phase
        description: Task description for the agent
        context_content: Content from previous phases for context
        auto_approve: If True, auto-approve the phase

    Returns:
        The phase output content
    """
    log_message(feat_id, f"Executing phase: {phase.value}")

    # Create task for this phase
    task = Task(
        description=description,
        expected_output=f"Structured {phase.value} specification",
        agent=agent,
    )

    # Create single-task crew for this phase
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    # Execute the task
    result = crew.kickoff()

    # Extract output - try multiple approaches
    content = ""
    if hasattr(result, 'raw') and result.raw:
        content = str(result.raw)
    elif hasattr(result, 'tasks_output') and result.tasks_output:
        # Get the first (and only) task output
        task_output = result.tasks_output[0]
        if hasattr(task_output, 'raw'):
            content = str(task_output.raw)
        else:
            content = str(task_output)
    else:
        content = str(result)

    log_message(feat_id, f"Phase {phase.value} generated {len(content)} characters of output")

    # Write spec file
    status = PhaseStatus.COMPLETED if auto_approve else PhaseStatus.PENDING_APPROVAL
    write_phase_spec(project_name, feat_id, phase, content, status=status)
    log_message(feat_id, f"Wrote spec file for phase: {phase.value}")

    # Update database status
    update_feature_status(feat_id, PhaseStatus.IN_PROGRESS, phase)

    # Auto-approve if requested
    if auto_approve:
        update_phase_status(
            project_name, feat_id, phase, PhaseStatus.COMPLETED, comment="Auto-approved", user="system"
        )

    return content


def run_workflow(
    feat_id: str,
    project_name: str,
    description: str,
    project_id: int,
    auto_approve: bool = False,
) -> dict:
    """
    Run the full workflow for a feature.

    Args:
        feat_id: The feature ID
        project_name: Name of the project
        description: Feature description
        project_id: Database project ID
        auto_approve: If True, auto-approve each phase (for one-shot execution)

    Returns:
        Workflow result dictionary
    """
    log_message(feat_id, f"Starting workflow for {feat_id}: {description}")

    results = {}
    phase_outputs = {}  # Store outputs for context in later phases

    try:
        # Create agents once for all phases
        analyst = create_requirements_analyst()
        architect = create_architect()
        planner = create_task_planner()
        developer = create_developer()
        qa = create_qa_engineer()
        reviewer = create_reviewer()

        # Update status to in_progress
        update_feature_status(feat_id, PhaseStatus.IN_PROGRESS, WorkflowPhase.REQUIREMENTS)

        # Phase 1: Requirements
        log_message(feat_id, "Phase 1/6: Gathering requirements")
        requirements_desc = f"""Analyze the following feature request and create comprehensive requirements:

Feature: {description}
Project: {project_name}
Feature ID: {feat_id}

Create a requirements specification that includes:
1. Functional requirements (what the feature should do)
2. Non-functional requirements (performance, security, etc.)
3. User stories or use cases
4. Acceptance criteria
5. Dependencies and constraints
6. Out of scope items

Output the requirements as a structured YAML-compatible specification."""

        phase_outputs['requirements'] = execute_phase(
            feat_id, project_name, WorkflowPhase.REQUIREMENTS,
            analyst, requirements_desc, auto_approve=auto_approve
        )
        results['requirements'] = {"status": "completed" if auto_approve else "pending_approval"}

        # Phase 2: Design
        log_message(feat_id, "Phase 2/6: Creating architectural design")
        design_desc = f"""Based on the requirements, create an architectural design:

Feature: {description}
Feature ID: {feat_id}
Project: {project_name}

Previous Phase - Requirements:
{phase_outputs['requirements'][:2000]}

The design should include:
1. High-level architecture overview
2. Component diagram (in Mermaid format)
3. Data models and schemas
4. API contracts (if applicable)
5. Integration points with existing code
6. Technology decisions and rationale

Output as a structured design document."""

        phase_outputs['design'] = execute_phase(
            feat_id, project_name, WorkflowPhase.DESIGN,
            architect, design_desc, phase_outputs['requirements'], auto_approve
        )
        results['design'] = {"status": "completed" if auto_approve else "pending_approval"}

        # Phase 3: Tasks
        log_message(feat_id, "Phase 3/6: Breaking down into tasks")
        tasks_desc = f"""Break down the design into implementation tasks:

Feature ID: {feat_id}
Project: {project_name}

Previous Phase - Design:
{phase_outputs['design'][:2000]}

Create a task list that includes:
1. Task ID and title
2. Description and acceptance criteria
3. Files to create or modify
4. Dependencies on other tasks
5. Estimated complexity (low/medium/high)
6. Test requirements

Output as a structured task list."""

        phase_outputs['tasks'] = execute_phase(
            feat_id, project_name, WorkflowPhase.TASKS,
            planner, tasks_desc, phase_outputs['design'], auto_approve
        )
        results['tasks'] = {"status": "completed" if auto_approve else "pending_approval"}

        # Phase 4: Implementation
        log_message(feat_id, "Phase 4/6: Implementing feature")
        impl_desc = f"""Implement the feature according to the task breakdown:

Feature ID: {feat_id}
Project: {project_name}
Project Path: /projects/{project_name}

Previous Phase - Tasks:
{phase_outputs['tasks'][:2000]}

For each task:
1. Read existing code to understand context
2. Write or modify code as needed
3. Write tests for new functionality
4. Commit changes with clear messages
5. Document any deviations from the plan

Follow coding standards and best practices."""

        phase_outputs['implementation'] = execute_phase(
            feat_id, project_name, WorkflowPhase.IMPLEMENTATION,
            developer, impl_desc, phase_outputs['tasks'], auto_approve
        )
        results['implementation'] = {"status": "completed" if auto_approve else "pending_approval"}

        # Phase 5: Verification
        log_message(feat_id, "Phase 5/6: Verifying implementation")
        verify_desc = f"""Verify the implementation:

Feature ID: {feat_id}
Project: {project_name}
Project Path: /projects/{project_name}

Original Requirements:
{phase_outputs['requirements'][:1000]}

Implementation Summary:
{phase_outputs['implementation'][:1000]}

Verification steps:
1. Run all tests and report results
2. Verify each requirement is met
3. Check for edge cases
4. Identify any bugs or issues
5. Validate code quality

Report findings with pass/fail status for each item."""

        phase_outputs['verification'] = execute_phase(
            feat_id, project_name, WorkflowPhase.VERIFICATION,
            qa, verify_desc, phase_outputs['implementation'], auto_approve
        )
        results['verification'] = {"status": "completed" if auto_approve else "pending_approval"}

        # Phase 6: Review
        log_message(feat_id, "Phase 6/6: Reviewing implementation")
        review_desc = f"""Review the implementation:

Feature ID: {feat_id}
Project: {project_name}

Implementation Summary:
{phase_outputs['implementation'][:1000]}

Verification Results:
{phase_outputs['verification'][:1000]}

Review for:
1. Code quality and maintainability
2. Adherence to design patterns
3. Security considerations
4. Performance implications
5. Documentation completeness
6. Improvement suggestions

Provide constructive feedback with specific recommendations."""

        phase_outputs['review'] = execute_phase(
            feat_id, project_name, WorkflowPhase.REVIEW,
            reviewer, review_desc, phase_outputs['verification'], auto_approve
        )
        results['review'] = {"status": "completed" if auto_approve else "pending_approval"}

        # Mark workflow as complete
        final_status = PhaseStatus.COMPLETED if auto_approve else PhaseStatus.PENDING_APPROVAL
        update_feature_status(feat_id, final_status, WorkflowPhase.REVIEW)

        log_message(feat_id, f"Workflow completed successfully with status: {final_status.value}")

        return {
            "success": True,
            "feat_id": feat_id,
            "status": final_status.value,
            "phases": results,
        }

    except Exception as e:
        error_msg = f"Workflow error: {str(e)}"
        log_message(feat_id, error_msg, level="error")
        update_feature_status(feat_id, PhaseStatus.REJECTED, None)

        return {
            "success": False,
            "feat_id": feat_id,
            "error": error_msg,
        }


def start_workflow_async(
    feat_id: str,
    project_name: str,
    description: str,
    project_id: int,
    auto_approve: bool = False,
) -> None:
    """Start workflow in a background thread."""

    def run():
        run_workflow(feat_id, project_name, description, project_id, auto_approve)

    thread = Thread(target=run, daemon=True)
    thread.start()


class WorkflowManager:
    """Manager for tracking and controlling workflows."""

    def __init__(self):
        self._workflows: dict[str, dict] = {}

    def start(
        self,
        feat_id: str,
        project_name: str,
        description: str,
        project_id: int,
        auto_approve: bool = False,
    ) -> None:
        """Start a new workflow."""
        self._workflows[feat_id] = {
            "status": "running",
            "project": project_name,
            "description": description,
        }
        start_workflow_async(feat_id, project_name, description, project_id, auto_approve)

    def get_status(self, feat_id: str) -> Optional[dict]:
        """Get workflow status."""
        feature = get_feature(feat_id)
        if not feature:
            return None

        return {
            "feat_id": feat_id,
            "status": feature.status.value,
            "current_phase": feature.current_phase.value,
        }

    def list_running(self) -> list[str]:
        """List all running workflow IDs."""
        return [
            fid for fid, data in self._workflows.items()
            if data.get("status") == "running"
        ]


# Global workflow manager instance
workflow_manager = WorkflowManager()
