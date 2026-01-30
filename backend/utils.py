"""
Utility functions for ClaudeForge.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from db import get_next_feature_number
from models import Approval, PhaseStatus, SpecPhase, WorkflowPhase

PROJECTS_PATH = os.getenv("PROJECTS_PATH", "/projects")


def generate_feat_id() -> str:
    """
    Generate a unique feature ID in format FEAT-YYYYMMDD-NNN.
    NNN is incremented via SQLite counter.
    """
    today = datetime.utcnow().strftime("%Y%m%d")
    number = get_next_feature_number()
    return f"FEAT-{today}-{number:03d}"


def get_spec_dir(project_name: str, feat_id: str) -> Path:
    """Get the spec directory path for a feature."""
    return Path(PROJECTS_PATH) / project_name / ".spec-workflow" / "specs" / feat_id


def ensure_spec_dir(project_name: str, feat_id: str) -> Path:
    """Ensure spec directory exists and return path."""
    spec_dir = get_spec_dir(project_name, feat_id)
    spec_dir.mkdir(parents=True, exist_ok=True)
    return spec_dir


def get_phase_file(project_name: str, feat_id: str, phase: WorkflowPhase) -> Path:
    """Get the file path for a phase spec."""
    spec_dir = get_spec_dir(project_name, feat_id)
    return spec_dir / f"phase-{phase.value}.yaml"


def write_phase_spec(
    project_name: str,
    feat_id: str,
    phase: WorkflowPhase,
    content: str,
    status: PhaseStatus = PhaseStatus.DRAFT,
    dependencies: Optional[list[str]] = None,
) -> SpecPhase:
    """Write a phase specification to YAML file."""
    ensure_spec_dir(project_name, feat_id)
    phase_file = get_phase_file(project_name, feat_id, phase)

    now = datetime.utcnow()
    spec = SpecPhase(
        feature_id=feat_id,
        phase=phase,
        status=status,
        content=content,
        approvals=[
            Approval(user="system", timestamp=now, comment="Auto-generated")
        ],
        dependencies=dependencies or [],
        created_at=now,
        updated_at=now,
    )

    # Convert to dict for YAML
    spec_dict = {
        "feature_id": spec.feature_id,
        "phase": spec.phase.value,
        "status": spec.status.value,
        "content": spec.content,
        "approvals": [
            {
                "user": a.user,
                "timestamp": a.timestamp.isoformat(),
                "comment": a.comment,
            }
            for a in spec.approvals
        ],
        "dependencies": spec.dependencies,
        "created_at": spec.created_at.isoformat(),
        "updated_at": spec.updated_at.isoformat(),
    }

    with open(phase_file, "w") as f:
        yaml.dump(spec_dict, f, default_flow_style=False, sort_keys=False)

    return spec


def read_phase_spec(project_name: str, feat_id: str, phase: WorkflowPhase) -> Optional[SpecPhase]:
    """Read a phase specification from YAML file."""
    phase_file = get_phase_file(project_name, feat_id, phase)

    if not phase_file.exists():
        return None

    with open(phase_file) as f:
        data = yaml.safe_load(f)

    return SpecPhase(
        feature_id=data["feature_id"],
        phase=WorkflowPhase(data["phase"]),
        status=PhaseStatus(data["status"]),
        content=data.get("content", ""),
        approvals=[
            Approval(
                user=a["user"],
                timestamp=datetime.fromisoformat(a["timestamp"]),
                comment=a.get("comment", ""),
            )
            for a in data.get("approvals", [])
        ],
        dependencies=data.get("dependencies", []),
        created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
        updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
    )


def update_phase_status(
    project_name: str,
    feat_id: str,
    phase: WorkflowPhase,
    status: PhaseStatus,
    comment: str = "",
    user: str = "system",
) -> Optional[SpecPhase]:
    """Update the status of a phase spec and add approval record."""
    spec = read_phase_spec(project_name, feat_id, phase)
    if not spec:
        return None

    spec.status = status
    spec.updated_at = datetime.utcnow()
    spec.approvals.append(
        Approval(user=user, timestamp=datetime.utcnow(), comment=comment)
    )

    phase_file = get_phase_file(project_name, feat_id, phase)
    spec_dict = {
        "feature_id": spec.feature_id,
        "phase": spec.phase.value,
        "status": spec.status.value,
        "content": spec.content,
        "approvals": [
            {
                "user": a.user,
                "timestamp": a.timestamp.isoformat(),
                "comment": a.comment,
            }
            for a in spec.approvals
        ],
        "dependencies": spec.dependencies,
        "created_at": spec.created_at.isoformat(),
        "updated_at": spec.updated_at.isoformat(),
    }

    with open(phase_file, "w") as f:
        yaml.dump(spec_dict, f, default_flow_style=False, sort_keys=False)

    return spec


def get_all_phase_specs(project_name: str, feat_id: str) -> dict[str, SpecPhase]:
    """Get all phase specs for a feature."""
    specs = {}
    for phase in WorkflowPhase:
        spec = read_phase_spec(project_name, feat_id, phase)
        if spec:
            specs[phase.value] = spec
    return specs


def scan_projects() -> list[str]:
    """Scan the projects directory for available projects."""
    projects_dir = Path(PROJECTS_PATH)
    if not projects_dir.exists():
        return []

    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            projects.append(item.name)

    return sorted(projects)


def get_project_features(project_name: str) -> list[str]:
    """Get all feature IDs for a project."""
    spec_base = Path(PROJECTS_PATH) / project_name / ".spec-workflow" / "specs"
    if not spec_base.exists():
        return []

    features = []
    for item in spec_base.iterdir():
        if item.is_dir() and item.name.startswith("FEAT-"):
            features.append(item.name)

    return sorted(features, reverse=True)


def calculate_progress(feat_id: str, project_name: str) -> float:
    """Calculate workflow progress as a float 0.0 to 1.0."""
    phases = list(WorkflowPhase)
    total = len(phases)
    completed = 0

    for phase in phases:
        spec = read_phase_spec(project_name, feat_id, phase)
        if spec and spec.status == PhaseStatus.COMPLETED:
            completed += 1
        elif spec and spec.status == PhaseStatus.IN_PROGRESS:
            completed += 0.5
        elif spec and spec.status == PhaseStatus.APPROVED:
            completed += 0.75

    return completed / total


def validate_feature_id(feat_id: str) -> bool:
    """Validate feature ID format."""
    pattern = r"^FEAT-\d{8}-\d{3}$"
    return bool(re.match(pattern, feat_id))


def backup_spec(project_name: str, feat_id: str, phase: WorkflowPhase) -> Optional[Path]:
    """Create a backup of a phase spec before modification."""
    phase_file = get_phase_file(project_name, feat_id, phase)
    if not phase_file.exists():
        return None

    backup_dir = get_spec_dir(project_name, feat_id) / ".backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"phase-{phase.value}_{timestamp}.yaml"

    import shutil
    shutil.copy2(phase_file, backup_file)

    return backup_file
