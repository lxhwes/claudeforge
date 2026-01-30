"""
Database operations for ClaudeForge using SQLite.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from models import (
    Feature,
    LogEntry,
    PhaseStatus,
    Project,
    ProjectStatus,
    WorkflowPhase,
)

DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/db.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id TEXT UNIQUE NOT NULL,
    project_id INTEGER NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    current_phase TEXT DEFAULT 'requirements',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    message TEXT,
    level TEXT DEFAULT 'info',
    FOREIGN KEY (feature_id) REFERENCES features(feature_id)
);

CREATE TABLE IF NOT EXISTS feature_counter (
    date TEXT PRIMARY KEY,
    counter INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_features_project ON features(project_id);
CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);
CREATE INDEX IF NOT EXISTS idx_logs_feature ON logs(feature_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
"""


@contextmanager
def get_db():
    """Get database connection with context manager."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Initialize the database schema."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def register_project(name: str, path: str) -> Project:
    """Register a project, returning existing if already registered."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if exists
        cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
        row = cursor.fetchone()

        if row:
            return Project(
                id=row["id"],
                name=row["name"],
                path=row["path"],
                status=ProjectStatus(row["status"]),
            )

        # Insert new
        cursor.execute(
            "INSERT INTO projects (name, path, status) VALUES (?, ?, ?)",
            (name, path, ProjectStatus.ACTIVE.value),
        )
        conn.commit()

        return Project(
            id=cursor.lastrowid,
            name=name,
            path=path,
            status=ProjectStatus.ACTIVE,
        )


def get_project(name: str) -> Optional[Project]:
    """Get a project by name."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return None

        return Project(
            id=row["id"],
            name=row["name"],
            path=row["path"],
            status=ProjectStatus(row["status"]),
        )


def get_project_by_id(project_id: int) -> Optional[Project]:
    """Get a project by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return Project(
            id=row["id"],
            name=row["name"],
            path=row["path"],
            status=ProjectStatus(row["status"]),
        )


def list_projects() -> list[Project]:
    """List all projects."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY name")
        rows = cursor.fetchall()

        return [
            Project(
                id=row["id"],
                name=row["name"],
                path=row["path"],
                status=ProjectStatus(row["status"]),
            )
            for row in rows
        ]


def create_feature(feature_id: str, project_id: int, description: str) -> Feature:
    """Create a new feature record."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO features
               (feature_id, project_id, description, status, current_phase)
               VALUES (?, ?, ?, ?, ?)""",
            (
                feature_id,
                project_id,
                description,
                PhaseStatus.DRAFT.value,
                WorkflowPhase.REQUIREMENTS.value,
            ),
        )
        conn.commit()

        return Feature(
            id=cursor.lastrowid,
            feature_id=feature_id,
            project_id=project_id,
            description=description,
            status=PhaseStatus.DRAFT,
            current_phase=WorkflowPhase.REQUIREMENTS,
        )


def get_feature(feature_id: str) -> Optional[Feature]:
    """Get a feature by feature_id."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM features WHERE feature_id = ?", (feature_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return Feature(
            id=row["id"],
            feature_id=row["feature_id"],
            project_id=row["project_id"],
            description=row["description"],
            status=PhaseStatus(row["status"]),
            current_phase=WorkflowPhase(row["current_phase"]),
        )


def update_feature_status(
    feature_id: str, status: PhaseStatus, phase: Optional[WorkflowPhase] = None
) -> bool:
    """Update feature status and optionally the current phase."""
    with get_db() as conn:
        cursor = conn.cursor()

        if phase:
            cursor.execute(
                "UPDATE features SET status = ?, current_phase = ? WHERE feature_id = ?",
                (status.value, phase.value, feature_id),
            )
        else:
            cursor.execute(
                "UPDATE features SET status = ? WHERE feature_id = ?",
                (status.value, feature_id),
            )

        conn.commit()
        return cursor.rowcount > 0


def list_features_by_project(project_id: int) -> list[Feature]:
    """List all features for a project."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM features WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
        rows = cursor.fetchall()

        return [
            Feature(
                id=row["id"],
                feature_id=row["feature_id"],
                project_id=row["project_id"],
                description=row["description"],
                status=PhaseStatus(row["status"]),
                current_phase=WorkflowPhase(row["current_phase"]),
            )
            for row in rows
        ]


def add_log(feature_id: str, message: str, level: str = "info") -> LogEntry:
    """Add a log entry for a feature."""
    with get_db() as conn:
        cursor = conn.cursor()
        timestamp = datetime.utcnow()
        cursor.execute(
            "INSERT INTO logs (feature_id, timestamp, message, level) VALUES (?, ?, ?, ?)",
            (feature_id, timestamp, message, level),
        )
        conn.commit()

        return LogEntry(
            id=cursor.lastrowid,
            feature_id=feature_id,
            timestamp=timestamp,
            message=message,
            level=level,
        )


def get_logs(feature_id: str, limit: int = 100) -> list[LogEntry]:
    """Get logs for a feature."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM logs
               WHERE feature_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (feature_id, limit),
        )
        rows = cursor.fetchall()

        return [
            LogEntry(
                id=row["id"],
                feature_id=row["feature_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                message=row["message"],
                level=row["level"],
            )
            for row in rows
        ]


def get_next_feature_number() -> int:
    """Get the next feature number for today's date."""
    today = datetime.utcnow().strftime("%Y%m%d")

    with get_db() as conn:
        cursor = conn.cursor()

        # Get current counter for today
        cursor.execute(
            "SELECT counter FROM feature_counter WHERE date = ?", (today,)
        )
        row = cursor.fetchone()

        if row:
            next_num = row["counter"] + 1
            cursor.execute(
                "UPDATE feature_counter SET counter = ? WHERE date = ?",
                (next_num, today),
            )
        else:
            next_num = 1
            cursor.execute(
                "INSERT INTO feature_counter (date, counter) VALUES (?, ?)",
                (today, next_num),
            )

        conn.commit()
        return next_num
