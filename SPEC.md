# Project Specification: ClaudeForge

## Overview

### Project Name
ClaudeForge

### Description
ClaudeForge is a Docker-based, spec-driven AI agent framework for software development workflows, built exclusively on Anthropic's Claude models. It leverages the Claude Agent SDK for native agent capabilities, CrewAI for multi-agent orchestration, and a modern web dashboard using SvelteKit with shadcn-svelte components. The framework enables structured development processes through autonomous agents, with human oversight via a local dashboard for spec approvals, monitoring, and visualizations.

This specification is exhaustively comprehensive, designed for one-shot implementation using Claude Code Opus 4.5. It includes all necessary details: file structures, code snippets, configurations, setup instructions, error handling, testing strategies, and sample workflows. The goal is to produce a working prototype that can be Dockerized, started via `./start.sh`, and used to process a sample feature request end-to-end.

Assume the implementer (Claude Code) has access to standard development tools, Git, and the Anthropic API. The prototype should be functional with placeholder Anthropic API keys (prompt user to set via env vars). Focus on core functionality first, then polish.

### Goals
- **Agentic Efficiency**: Parallel, autonomous workflows using Claude-powered agents for phases: Requirements → Design → Tasks → Implementation → Verification → Review.
- **Spec-Driven Focus**: Specifications as first-class YAML/Markdown artifacts in repo directories, with approval gates.
- **Scalability**: Multi-repo support, handling up to 20 mounted projects; large contexts via Claude's capabilities.
- **Usability**: Intuitive dashboard with real-time updates, approvals, and visualizations.
- **Claude-Native**: Use only Anthropic Claude models (Opus for orchestration/manager, Sonnet for subagents, Haiku for lightweight tasks like quick reviews).
- **Security & Reliability**: Local-only access, error recovery via agent self-reflection, secure API key handling.
- **Open-Source Friendly**: MIT license; modular code for extensions.

### Non-Goals
- Production hardening (e.g., no cloud deployment, advanced auth beyond local).
- Support for non-Claude LLMs.
- Custom ML training or external databases beyond SQLite for dashboard state.
- Mobile/responsive dashboard (desktop-first for prototype).

### Target Audience
- Solo developers or small teams using AI for spec-driven coding.
- Projects with complex features spanning multiple repos.

### Assumptions for Prototype
- Host machine: Docker and Docker Compose installed.
- User provides Anthropic API key via `.env` or env vars.
- Mounted repos: Assume ~/github/ with sample repos for testing.
- Prototype success: Can process a sample feature (e.g., "Add user auth to backend") through full workflow, with dashboard approvals.

## Architecture

### High-Level Diagram (ASCII)
```
Host Machine
    |
    +-- ~/github/
          |
          +-- claudeforge/             <-- This repo (git init here)
          |     +-- .env.example       <-- API keys, etc.
          |     +-- docker-compose.yml
          |     +-- Dockerfile-agent   <-- For agent container
          |     +-- Dockerfile-dashboard <-- For dashboard
          |     +-- start.sh           <-- CLI entrypoint
          |     +-- backend/           <-- Python: agents, API
          |     +-- frontend/          <-- SvelteKit: dashboard
          |     +-- .claude/           <-- Configs, rules (Markdown)
          |     +-- docs/              <-- QUICKSTART.md, etc.
          |     +-- tests/             <-- Pytest/Vitest
          |
          +-- sample-project/          <-- Mounted test repo
          +-- another-project/

                      |
                      | docker-compose up --build
                      v

+----------------------------------------------------------+
|                    Docker Environment                     |
|                                                          |
|  +------------------------+   +----------------------+   |
|  | claudeforge-agent      |   | claudeforge-dashboard|   |
|  |                        |   |                      |   |
|  | - CrewAI Orchestrator  |   | - SvelteKit Server   |   |
|  | - Claude Subagents     |   | - shadcn-svelte UI   |   |
|  | - FastAPI API          |   | - WebSockets         |   |
|  | - SQLite DB            |   | - API Client         |   |
|  | - /projects/ mount     |   |                      |   |
|  +------------------------+   +----------------------+   |
|            |                           |                 |
|            +-----------+---------------+                 |
|                        |                                 |
|              Shared Vol: /projects/ (host ~/github/)     |
|              API: http://agent:8000 (internal)           |
|              WS: ws://agent:8000/ws                      |
+----------------------------------------------------------+
```

- **claudeforge-agent**: Python container for orchestration, agents, API, and SQLite.
- **claudeforge-dashboard**: Node.js container for SvelteKit UI, proxies to agent API.
- **Communication**: Dashboard → API/WebSockets on agent container (internal networking).
- **Volumes**: /projects/ for read/write access to mounted repos.
- **Ports**: Exposed: 5050 (dashboard), internal: 8000 (API).

### Key Components Breakdown
1. **Orchestrator**: CrewAI Manager Agent (Claude Opus); dynamically routes tasks, handles approvals (pauses for dashboard input).
2. **Subagents**: CrewAI Agents (Claude Sonnet/Haiku); role-specific with tools (file I/O, Git, test runners).
3. **Specs**: Per-repo structure: `/projects/<repo>/.spec-workflow/specs/<FEAT-ID>/phase-<phase>.yaml` (e.g., phase-requirements.yaml).
4. **Dashboard**: SvelteKit app with reactive stores for real-time; shadcn-svelte for UI primitives.
5. **API**: FastAPI for CRUD operations on specs/projects; WebSockets for streaming agent logs/progress.
6. **CLI**: `./start.sh` for Docker ops; internal `claudeforge` CLI (Typer) for workflow initiation inside container.

## Requirements

### Functional Requirements
- **Workflow Initiation**:
  - CLI: `claudeforge start <project> <feature-desc>` or dashboard button.
  - Generate unique Feature ID (FEAT-YYYYMMDD-NNN, increment NNN via SQLite counter).
  - Create spec directory and initial draft.
- **Agent Phases** (Sequential with Parallel Subtasks Where Possible):
  - **Requirements**: Analyst agent clarifies user input, outputs YAML spec.
  - **Design**: Architect agent proposes architecture, diagrams (Mermaid text).
  - **Tasks**: Planner breaks into subtasks, assigns to agents.
  - **Implementation**: Developer agent edits files, commits via Git.
  - **Verification**: QA runs tests (e.g., pytest if Python project), reports issues.
  - **Review**: Reviewer suggests improvements; loop back if needed.
  - Pause at each phase end for dashboard approval.
- **Dashboard Features**:
  - Home: List projects (scan /projects/, register in SQLite if new).
  - Project View: Tree browser for .spec-workflow/, spec previews (Markdown rendering).
  - Spec Detail: Editor (readonly for prototype), approval/reject buttons with comments.
  - Agent Monitor: Real-time timeline/logs, progress bar per phase, Mermaid workflow graph.
  - Search: Filter specs by ID/status/phase.
- **CLI Commands** (Inside Container):
  - `claudeforge status`: List running workflows.
  - `claudeforge verify`: Health check (API, DB).
- **Docker Enforcement**:
  - Agents validate Dockerfiles/Compose against standards (regex checks for multi-stage, non-root, etc.).
- **Error Handling**:
  - Agents: Self-reflection loops (CrewAI verbose=True) to retry on failures.
  - API: HTTP errors with JSON details.
  - Dashboard: Toast notifications for errors (shadcn-svelte Toaster).

### Non-Functional Requirements
- **Performance**: <10s per phase for simple tasks; parallel subtasks via CrewAI.
- **Reliability**: Idempotent operations (e.g., retry failed Git commits); backups of specs before edits.
- **Security**: Env vars for API keys; no external exposure; non-root containers.
- **Maintainability**: Type hints (Pydantic), Svelte stores for state, comprehensive tests.
- **Compatibility**: Python 3.12, Node 20+; cross-platform Docker.

## Design

### Data Models
- **Spec YAML** (Per Phase File):
  ```yaml
  feature_id: FEAT-20260129-001
  phase: requirements  # or design, etc.
  status: draft|pending_approval|approved|rejected|in_progress|completed
  content: |  # Markdown
    ## Requirements
    - User auth with JWT
  approvals: 
    - user: system
      timestamp: 2026-01-29T20:00:00Z
      comment: Auto-generated
  dependencies: [FEAT-20260128-001]  # Optional cross-feature links
  ```
- **SQLite Schema** (db.sqlite in agent container):
  ```sql
  CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    status TEXT DEFAULT 'active'
  );

  CREATE TABLE features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id TEXT UNIQUE NOT NULL,  -- e.g., FEAT-20260129-001
    project_id INTEGER NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    FOREIGN KEY (project_id) REFERENCES projects(id)
  );

  CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    message TEXT,
    FOREIGN KEY (feature_id) REFERENCES features(feature_id)
  );
  ```
- **Agent Task** (CrewAI):
  - Internal: Description str, expected_output str, tools list.

### API Endpoints (FastAPI at /api/)
- **Projects**:
  - GET /projects/list → [{"id":1, "name":"sample-project", "path":"/projects/sample-project"}]
  - POST /projects/register → {name: str, path: str} → Registers if new.
- **Specs**:
  - GET /specs/{project}/{feat_id} → Returns aggregated spec data (all phases).
  - POST /specs/approve → {feat_id: str, phase: str, action: "approve"|"reject", comment: str} → Updates status, resumes agent.
- **Agents**:
  - POST /agents/start → {project: str, feature_desc: str} → Kicks off CrewAI crew, returns feat_id.
  - GET /agents/status/{feat_id} → {status: str, progress: float (0-1), logs: [str]}
- **Health**:
  - GET /health → {"status": "ok"}
- **WebSocket**:
  - /ws/logs/{feat_id} → Streams JSON {message: str, level: "info"|"error"}.

### Frontend (SvelteKit)
- **File Structure**:
  ```
  frontend/
  ├── src/
  │   ├── app.html
  │   ├── routes/
  │   │   ├── +layout.svelte  # Nav, Sidebar, Toaster
  │   │   ├── +page.svelte    # Home: Project list (Table)
  │   │   ├── projects/[slug]/+page.svelte  # Project specs tree (Accordion)
  │   │   ├── specs/[feat_id]/+page.svelte  # Spec viewer (Tabs for phases), Approval Modal
  │   │   └── agents/+page.svelte  # Monitor: Timeline, Logs (Terminal-like), Mermaid graph
  │   ├── lib/
  │   │   ├── components/     # shadcn-svelte: Button, Table, Modal, etc.
  │   │   ├── stores/         # api.js (fetch wrapper), websocket.js, projects.js (writable store)
  │   │   └── utils/          # markdownRenderer.svelte, mermaidRenderer.svelte
  │   └── app.css             # Tailwind
  ├── svelte.config.js
  ├── vite.config.js
  ├── package.json            # Dependencies: @sveltejs/kit, shadcn-svelte, tailwindcss, etc.
  └── static/                 # Assets if needed
  ```
- **Key Code Snippets**:
  - Store Example (stores/api.js):
    ```javascript
    import { writable } from 'svelte/store';
    export const projects = writable([]);

    export async function fetchProjects() {
      const res = await fetch('http://localhost:8000/api/projects/list');
      const data = await res.json();
      projects.set(data);
    }
    ```
  - WebSocket Store (stores/websocket.js):
    ```javascript
    import { writable } from 'svelte/store';
    export const logs = writable([]);

    let ws;
    export function connectWS(featId) {
      ws = new WebSocket(`ws://localhost:8000/ws/logs/${featId}`);
      ws.onmessage = (event) => {
        logs.update(l => [...l, JSON.parse(event.data)]);
      };
    }
    ```
  - Approval Modal (in specs/[feat_id]/+page.svelte):
    ```svelte
    <script>
      import { Button } from '$lib/components/ui/button';
      import { Modal } from '$lib/components/ui/modal';
      let showModal = false;
    </script>

    <Button on:click={() => showModal = true}>Approve</Button>
    {#if showModal}
      <Modal>
        <textarea bind:value={comment}></textarea>
        <Button on:click={handleApprove}>Submit</Button>
      </Modal>
    {/if}
    ```
  - Mermaid Integration: Use @braintree/sanitize-url for safe rendering; display workflow graphs.

### Backend (Python)
- **File Structure**:
  ```
  backend/
  ├── main.py                 # FastAPI app, WebSockets
  ├── agents.py               # CrewAI definitions
  ├── tools.py                # Custom tools: file_edit, git_commit, etc.
  ├── models.py               # Pydantic: SpecModel, etc.
  ├── db.py                   # SQLite connection, queries
  ├── cli.py                  # Typer CLI
  ├── requirements.txt        # anthropic, crewai, fastapi[all], uvicorn, pydantic, typer, sqlite3
  └── utils.py                # Feature ID generator, spec writer
  ```
- **Key Code Snippets**:
  - FastAPI (main.py):
    ```python
    from fastapi import FastAPI, WebSocket
    from pydantic import BaseModel
    import uvicorn
    from .db import get_db, register_project
    from .agents import start_crew

    app = FastAPI()

    class StartWorkflow(BaseModel):
        project: str
        feature_desc: str

    @app.post("/api/agents/start")
    async def start_agents(data: StartWorkflow):
        feat_id = utils.generate_feat_id()
        # Register project if new
        db = get_db()
        project_id = register_project(db, data.project, f"/projects/{data.project}")
        # Start CrewAI in background thread
        import threading
        threading.Thread(target=start_crew, args=(feat_id, data.feature_desc, project_id)).start()
        return {"feat_id": feat_id}

    @app.websocket("/ws/logs/{feat_id}")
    async def websocket_endpoint(websocket: WebSocket, feat_id: str):
        await websocket.accept()
        # Simulate or hook into CrewAI logs
        while True:
            log = await get_log_queue(feat_id)  # Implement queue
            await websocket.send_json({"message": log})

    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)
    ```
  - CrewAI Agents (agents.py):
    ```python
    from crewai import Agent, Task, Crew
    from anthropic import Anthropic
    from .tools import file_tool, git_tool

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    orchestrator = Agent(
        role="Orchestrator",
        goal="Coordinate workflow",
        backstory="You manage approvals and routing.",
        llm=client,  # Opus via env var for model selection
        verbose=True,
        allow_delegation=True,
        tools=[file_tool]
    )

    requirements_analyst = Agent(
        role="Requirements Analyst",
        goal="Gather requirements",
        llm=client,  # Sonnet
        tools=[]
    )

    # Define other agents similarly

    def start_crew(feat_id, desc, project_id):
        tasks = [
            Task(description="Gather reqs", agent=requirements_analyst, expected_output="YAML spec"),
            # Add pauses for approval via callback to API
        ]
        crew = Crew(agents=[orchestrator, ...], tasks=tasks, manager_llm=client)
        result = crew.kickoff()
        # Log results, update DB
    ```
  - Tools (tools.py): Use CrewAI's @tool decorator for file read/write, Git ops (subprocess for git commands).
  - DB (db.py):
    ```python
    import sqlite3

    def get_db():
        conn = sqlite3.connect('db.sqlite')
        return conn

    def init_db():
        conn = get_db()
        # Execute schema SQL
        conn.executescript(SCHEMA)
    ```
  - CLI (cli.py):
    ```python
    import typer
    app = typer.Typer()

    @app.command()
    def start(project: str, feature_desc: str):
        # Call API internally

    if __name__ == "__main__":
        app()
    ```

### Docker Setup
- **Dockerfile-agent** (Multi-Stage):
  ```dockerfile
  # Build stage
  FROM python:3.12-slim AS builder
  WORKDIR /app
  COPY backend/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Final stage
  FROM python:3.12-slim
  WORKDIR /app
  COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
  COPY backend/ .
  RUN useradd -m codeuser
  USER codeuser
  EXPOSE 8000
  HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- **Dockerfile-dashboard**:
  ```dockerfile
  FROM node:20-alpine
  WORKDIR /app
  COPY frontend/package*.json .
  RUN npm install
  COPY frontend/ .
  RUN npm run build
  EXPOSE 5050
  HEALTHCHECK CMD curl -f http://localhost:5050 || exit 1
  CMD ["npm", "run", "preview", "--", "--host", "--port", "5050"]
  ```
- **docker-compose.yml**:
  ```yaml
  version: '3.8'
  services:
    agent:
      build: {context: ., dockerfile: Dockerfile-agent}
      volumes:
        - ~/github:/projects
        - ./.env:/app/.env
      ports:
        - "8000:8000"  # For dev access
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
        interval: 30s
        timeout: 10s
        retries: 3
      environment:
        - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

    dashboard:
      build: {context: ., dockerfile: Dockerfile-dashboard}
      ports:
        - "5050:5050"
      depends_on:
        agent: {condition: service_healthy}
  ```
- **start.sh** (Bash):
  ```bash
  #!/bin/bash
  case "$1" in
    --build) docker-compose up --build ;;
    --stop) docker-compose down ;;
    --restart) docker-compose restart ;;
    --logs) docker-compose logs ;;
    --status) docker-compose ps ;;
    --setup-auth) echo "Set ANTHROPIC_API_KEY in .env" ;;
    *) docker-compose up ;;
  esac
  ```

### .claude/ Directory
- agents.json: JSON config for agent models (e.g., {"orchestrator": "claude-3-opus-20240229"}).
- rules/: Markdown files (e.g., docker-standards.md) – agents reference these for enforcement.

### Docs
- **QUICKSTART.md**:
  ```
  # Quick Start
  cp .env.example .env
  # Add API key
  ./start.sh --build
  docker exec -it claudeforge-agent bash
  cd /projects/sample-project
  claudeforge start sample-project "Add auth feature"
  # Open http://localhost:5050
  ```
- **WORKFLOW.md**: Detail phases, how to approve.
- **TROUBLESHOOTING.md**: Common issues (e.g., API key missing → error logs).

## Implementation Plan for One-Shot Prototype
1. **Setup Repo**: git init, add files per structures.
2. **Backend**: Implement db.py first (init_db on startup), then models, utils, tools, agents, main.py, cli.py.
3. **Frontend**: Init SvelteKit, add shadcn-svelte, implement stores/components/routes.
4. **Integration**: Hook dashboard to API; test WebSockets with sample logs.
5. **Docker**: Build/test containers; ensure mounts work.
6. **Sample Workflow**: Hardcode a test feature in tests/; run end-to-end.

## Testing Strategy
- **Backend**: Pytest (test_agents.py: mock Claude responses, assert spec files created).
- **Frontend**: Vitest (test components, stores).
- **E2E**: Docker up, curl API, browser test dashboard (manual for prototype; automate with Playwright later).
- **Coverage**: Aim 80%+ for core paths.

## License & Extras
- **LICENSE**: MIT text.
- **.gitignore**: Standard Python/Node (venv, node_modules, db.sqlite).
- **.env.example**:
  ```
  ANTHROPIC_API_KEY=sk-...
  CLAUDE_MODEL_OPUS=claude-3-opus-20240229
  CLAUDE_MODEL_SONNET=claude-3-sonnet-20240229
  CLAUDE_MODEL_HAIKU=claude-3-haiku-20240307
  ```
- **Extensions Ideas**: Add RAG for spec search (via Claude embeddings), cloud mode.
