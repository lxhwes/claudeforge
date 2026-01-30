"""
FastAPI main application for ClaudeForge API.
Provides REST endpoints and WebSocket streaming for agent workflows.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from agents import get_log_queue, workflow_manager
from db import (
    add_log,
    create_feature,
    get_feature,
    get_logs,
    get_project,
    get_project_by_id,
    init_db,
    list_features_by_project,
    list_projects,
    register_project,
)
from models import (
    AgentStatusResponse,
    ApproveSpecRequest,
    ApproveSpecResponse,
    Feature,
    HealthResponse,
    PhaseStatus,
    Project,
    ProjectListResponse,
    SpecResponse,
    StartWorkflowRequest,
    StartWorkflowResponse,
    WebSocketMessage,
    WorkflowPhase,
)
from utils import (
    calculate_progress,
    generate_feat_id,
    get_all_phase_specs,
    get_project_features,
    scan_projects,
    update_phase_status,
    validate_feature_id,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    # Auto-register projects from /projects directory
    for project_name in scan_projects():
        register_project(project_name, f"/projects/{project_name}")
    yield


app = FastAPI(
    title="ClaudeForge API",
    description="Docker-based AI Agent Framework for Spec-Driven Development",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to dashboard origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and database health."""
    try:
        # Quick DB check
        projects = list_projects()
        return HealthResponse(
            status="ok",
            version="0.1.0",
            database="connected",
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            version="0.1.0",
            database=f"error: {str(e)}",
        )


# Project endpoints
@app.get("/api/projects/list", response_model=ProjectListResponse, tags=["Projects"])
async def get_projects():
    """List all registered projects."""
    # Re-scan to pick up new projects
    for project_name in scan_projects():
        register_project(project_name, f"/projects/{project_name}")

    projects = list_projects()
    return ProjectListResponse(projects=projects)


@app.post("/api/projects/register", response_model=Project, tags=["Projects"])
async def register_new_project(name: str, path: str):
    """Register a new project."""
    project = register_project(name, path)
    return project


@app.get("/api/projects/{project_name}", response_model=Project, tags=["Projects"])
async def get_project_details(project_name: str):
    """Get project details by name."""
    project = get_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/api/projects/{project_name}/features", tags=["Projects"])
async def get_project_feature_list(project_name: str):
    """Get all features for a project."""
    project = get_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get features from both database and filesystem
    feature_ids = get_project_features(project_name)
    db_features = list_features_by_project(project.id)

    # Merge and deduplicate
    all_features = {f.feature_id: f for f in db_features}
    for fid in feature_ids:
        if fid not in all_features:
            all_features[fid] = Feature(
                feature_id=fid,
                project_id=project.id,
                description="(from filesystem)",
                status=PhaseStatus.DRAFT,
            )

    return {"features": list(all_features.values())}


# Spec endpoints
@app.get("/api/specs/{project_name}/{feat_id}", response_model=SpecResponse, tags=["Specs"])
async def get_spec(project_name: str, feat_id: str):
    """Get all phase specs for a feature."""
    if not validate_feature_id(feat_id):
        raise HTTPException(status_code=400, detail="Invalid feature ID format")

    project = get_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    feature = get_feature(feat_id)
    description = feature.description if feature else ""

    phases = get_all_phase_specs(project_name, feat_id)

    return SpecResponse(
        feature_id=feat_id,
        project_name=project_name,
        description=description,
        phases=phases,
    )


@app.post("/api/specs/approve", response_model=ApproveSpecResponse, tags=["Specs"])
async def approve_spec(request: ApproveSpecRequest):
    """Approve or reject a spec phase."""
    feature = get_feature(request.feat_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Get project name from feature
    project = get_project_by_id(feature.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine new status
    if request.action == "approve":
        new_status = PhaseStatus.APPROVED
    elif request.action == "reject":
        new_status = PhaseStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Update phase status
    spec = update_phase_status(
        project.name,
        request.feat_id,
        request.phase,
        new_status,
        comment=request.comment,
        user="dashboard",
    )

    if not spec:
        raise HTTPException(status_code=404, detail="Phase spec not found")

    # Log the action
    add_log(
        request.feat_id,
        f"Phase {request.phase.value} {request.action}d: {request.comment}",
    )

    return ApproveSpecResponse(
        success=True,
        message=f"Phase {request.phase.value} {request.action}d successfully",
    )


# Agent workflow endpoints
@app.post("/api/agents/start", response_model=StartWorkflowResponse, tags=["Agents"])
async def start_workflow(request: StartWorkflowRequest):
    """Start a new agent workflow for a feature."""
    # Validate project exists
    project = get_project(request.project)
    if not project:
        # Try to register it
        project = register_project(request.project, f"/projects/{request.project}")

    # Generate feature ID
    feat_id = generate_feat_id()

    # Create feature record
    create_feature(feat_id, project.id, request.feature_desc)

    # Start workflow (auto_approve=True for one-shot execution)
    auto_approve = os.getenv("AUTO_APPROVE", "true").lower() == "true"
    workflow_manager.start(
        feat_id,
        request.project,
        request.feature_desc,
        project.id,
        auto_approve=auto_approve,
    )

    return StartWorkflowResponse(
        feat_id=feat_id,
        message=f"Workflow started for {request.project}",
    )


@app.get("/api/agents/status/{feat_id}", response_model=AgentStatusResponse, tags=["Agents"])
async def get_workflow_status(feat_id: str):
    """Get status of a workflow."""
    if not validate_feature_id(feat_id):
        raise HTTPException(status_code=400, detail="Invalid feature ID format")

    feature = get_feature(feat_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Get project for progress calculation
    project = get_project_by_id(feature.project_id)
    project_name = project.name if project else ""

    # Get recent logs
    logs = get_logs(feat_id, limit=50)
    log_messages = [log.message for log in logs]

    return AgentStatusResponse(
        feat_id=feat_id,
        status=feature.status,
        current_phase=feature.current_phase,
        progress=calculate_progress(feat_id, project_name),
        logs=log_messages,
    )


@app.get("/api/agents/running", tags=["Agents"])
async def list_running_workflows():
    """List all currently running workflows."""
    running = workflow_manager.list_running()
    return {"running": running}


# WebSocket endpoint for real-time logs
@app.websocket("/ws/logs/{feat_id}")
async def websocket_logs(websocket: WebSocket, feat_id: str):
    """WebSocket endpoint for streaming logs."""
    await websocket.accept()

    if not validate_feature_id(feat_id):
        await websocket.close(code=4000, reason="Invalid feature ID")
        return

    queue = get_log_queue(feat_id)

    try:
        while True:
            # Check for new log messages
            try:
                # Non-blocking check with timeout
                await asyncio.sleep(0.1)

                if not queue.empty():
                    log_data = queue.get_nowait()
                    message = WebSocketMessage(
                        message=log_data.get("message", ""),
                        level=log_data.get("level", "info"),
                        timestamp=datetime.utcnow(),
                    )
                    await websocket.send_json(message.model_dump(mode="json"))

            except Exception:
                continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=4001, reason=str(e))


# Search endpoint
@app.get("/api/search", tags=["Search"])
async def search_specs(
    query: str = Query(..., min_length=1),
    project: Optional[str] = None,
    status: Optional[str] = None,
    phase: Optional[str] = None,
):
    """Search specs by various criteria."""
    results = []

    projects_to_search = [project] if project else [p.name for p in list_projects()]

    for proj_name in projects_to_search:
        feature_ids = get_project_features(proj_name)

        for feat_id in feature_ids:
            # Filter by query in feature ID
            if query.lower() not in feat_id.lower():
                continue

            feature = get_feature(feat_id)

            # Filter by status
            if status and feature and feature.status.value != status:
                continue

            # Filter by phase
            if phase and feature and feature.current_phase.value != phase:
                continue

            results.append({
                "project": proj_name,
                "feature_id": feat_id,
                "status": feature.status.value if feature else "unknown",
                "phase": feature.current_phase.value if feature else "unknown",
            })

    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
