# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

ClaudeForge is a Docker-based, spec-driven AI agent framework for software development workflows. It uses CrewAI for multi-agent orchestration with Claude models exclusively (Opus for orchestration, Sonnet for subagents, Haiku for lightweight tasks). The system implements a six-phase workflow (Requirements → Design → Tasks → Implementation → Verification → Review) with approval gates and real-time dashboard monitoring.

**Architecture**: Dockerized Python (FastAPI + CrewAI) backend with SvelteKit frontend dashboard connected via REST API and WebSockets.

## Development Setup

### Prerequisites
- Docker and Docker Compose installed
- Anthropic API key (set in `.env` file)
- Projects mounted to `~/github/` directory

### Environment Configuration
```bash
# Create .env from template
cp .env.example .env

# Edit .env and set:
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
CLAUDE_MODEL_OPUS=claude-3-opus-20240229
CLAUDE_MODEL_SONNET=claude-3-5-sonnet-20241022
CLAUDE_MODEL_HAIKU=claude-3-haiku-20240307
```

### Starting the System
```bash
# Build and start containers
./start.sh --build

# Start without rebuilding
./start.sh

# Stop containers
./start.sh --stop

# View logs
./start.sh --logs

# Open shell in agent container
./start.sh --shell
```

The dashboard will be available at `http://localhost:5050` and the API at `http://localhost:8000`.

## Testing

### Backend Tests (Python)
```bash
# Run all tests
docker-compose exec agent pytest

# Run with coverage
docker-compose exec agent pytest --cov=. --cov-report=html

# Run specific test file
docker-compose exec agent pytest tests/test_agents.py

# Run specific test
docker-compose exec agent pytest tests/test_api.py::test_health_check -v
```

Test files are in `tests/` directory using pytest framework. Configuration is in `pytest.ini`.

### Frontend Tests (JavaScript)
```bash
# Run frontend tests
docker-compose exec dashboard npm test

# Run with watch mode
docker-compose exec dashboard npm test -- --watch

# Run specific test file
docker-compose exec dashboard npm test -- src/lib/stores/api.test.js
```

Frontend tests use Vitest framework configured in `vitest.config.js`.

## CLI Commands

Inside the agent container (`./start.sh --shell`):

```bash
# Start a new workflow
claudeforge start <project-name> "Feature description"

# Check workflow status
claudeforge status <FEAT-ID>

# List all running workflows
claudeforge status

# View logs for a workflow
claudeforge logs <FEAT-ID> -n 100
claudeforge logs <FEAT-ID> --follow

# Approve/reject a phase
claudeforge approve <FEAT-ID> requirements -c "Looks good"
claudeforge reject <FEAT-ID> design -c "Needs revision"

# List projects
claudeforge projects

# Health check
claudeforge verify
```

## Core Architecture

### Backend Structure (`backend/`)
- **`main.py`**: FastAPI application with REST endpoints and WebSocket support
- **`agents.py`**: CrewAI agent definitions (Orchestrator, Analyst, Architect, Planner, Developer, QA, Reviewer)
- **`tools.py`**: CrewAI tools for file operations, Git commands, test runners
- **`models.py`**: Pydantic data models for API requests/responses and domain objects
- **`db.py`**: SQLite database operations (projects, features, logs)
- **`utils.py`**: Utility functions (spec file management, feature ID generation)
- **`cli.py`**: Typer CLI interface for workflow management

### Frontend Structure (`frontend/src/`)
- **`routes/`**: SvelteKit pages
  - `+page.svelte`: Home page with project list
  - `projects/[slug]/+page.svelte`: Project spec browser
  - `specs/[feat_id]/+page.svelte`: Spec viewer with approval interface
  - `agents/+page.svelte`: Agent monitor with real-time logs
- **`lib/components/`**: UI components (shadcn-svelte)
- **`lib/stores/`**: Svelte stores for API calls and WebSocket management
- **`lib/utils/`**: Helper utilities for markdown/Mermaid rendering

### Data Flow
1. User initiates workflow via dashboard or CLI
2. API creates feature record and generates unique `FEAT-YYYYMMDD-NNN` ID
3. CrewAI crew starts, delegating to specialized agents for each phase
4. Agents write phase specs to `.spec-workflow/specs/<FEAT-ID>/phase-*.yaml` in project directories
5. Workflow pauses at approval gates (if enabled)
6. WebSockets stream real-time logs to dashboard
7. SQLite database tracks projects, features, and logs

### Key Design Patterns
- **Spec-Driven Development**: Each workflow phase produces a YAML spec artifact stored in project repositories
- **Multi-Agent Orchestration**: CrewAI manages delegation between specialized Claude agents
- **Approval Gates**: Phases can pause for manual approval via dashboard or CLI
- **Real-time Streaming**: WebSockets push agent logs to dashboard for live monitoring

## Workflow Phases

The system implements six sequential phases:

1. **Requirements**: Analyst agent (Sonnet) gathers requirements → `phase-requirements.yaml`
2. **Design**: Architect agent (Sonnet) creates technical design with Mermaid diagrams → `phase-design.yaml`
3. **Tasks**: Planner agent (Sonnet) breaks design into tasks → `phase-tasks.yaml`
4. **Implementation**: Developer agent (Sonnet) writes code and commits to Git → `phase-implementation.yaml`
5. **Verification**: QA agent (Sonnet) runs tests and validates → `phase-verification.yaml`
6. **Review**: Reviewer agent (Haiku) provides feedback → `phase-review.yaml`

Each phase has status: `draft` → `pending_approval` → `approved` → `in_progress` → `completed` (or `rejected`)

## Spec File Structure

Located at: `<project>/.spec-workflow/specs/<FEAT-ID>/phase-<phase>.yaml`

```yaml
feature_id: FEAT-20260129-001
phase: requirements
status: pending_approval
content: |
  ## Requirements
  - Functional requirement 1
  - Non-functional requirement 2
approvals:
  - user: system
    timestamp: 2026-01-29T20:00:00Z
    comment: Auto-generated
dependencies: []
created_at: 2026-01-29T20:00:00Z
updated_at: 2026-01-29T20:00:00Z
```

## API Endpoints

**Health**
- `GET /health` - Health check with database status

**Projects**
- `GET /api/projects/list` - List all registered projects
- `POST /api/projects/register` - Register new project
- `GET /api/projects/{project_name}` - Get project details
- `GET /api/projects/{project_name}/features` - Get project's features

**Specs**
- `GET /api/specs/{project_name}/{feat_id}` - Get all phase specs for feature
- `POST /api/specs/approve` - Approve/reject a phase

**Agents**
- `POST /api/agents/start` - Start new workflow
- `GET /api/agents/status/{feat_id}` - Get workflow status with progress
- `GET /api/agents/running` - List running workflows

**WebSocket**
- `WS /ws/logs/{feat_id}` - Stream real-time logs for feature

## Database Schema

SQLite database at `/app/data/db.sqlite`:

```sql
-- Projects table
CREATE TABLE projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  path TEXT NOT NULL,
  status TEXT DEFAULT 'active'
);

-- Features table
CREATE TABLE features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feature_id TEXT UNIQUE NOT NULL,  -- FEAT-YYYYMMDD-NNN
  project_id INTEGER NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'draft',
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Logs table
CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feature_id TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  message TEXT,
  FOREIGN KEY (feature_id) REFERENCES features(feature_id)
);
```

## Docker Configuration

### Multi-Stage Build (Dockerfile-agent)
- Build stage: Install Python dependencies from `requirements.txt`
- Final stage: Copy installed packages, run as non-root user `codeuser`
- Healthcheck: `curl -f http://localhost:8000/health`

### Volume Mounts
- `~/github:/projects:rw` - Mounted projects (read-write)
- `./backend:/app:ro` - Backend code (read-only for hot reload)
- `agent-data:/app/data` - Persistent SQLite database

### Environment Variables
- `ANTHROPIC_API_KEY` - Required for Claude API access
- `CLAUDE_MODEL_*` - Model selection for different agent roles
- `DATABASE_PATH` - SQLite database location
- `PROJECTS_PATH` - Mounted projects directory
- `LOG_LEVEL` - Logging verbosity (INFO/DEBUG)

## Common Development Tasks

### Adding a New API Endpoint
1. Add Pydantic request/response models to `backend/models.py`
2. Implement endpoint in `backend/main.py`
3. Update frontend API store in `frontend/src/lib/stores/api.js`
4. Write tests in `tests/test_api.py`

### Adding a New Agent
1. Create agent function in `backend/agents.py` using `Agent()` constructor
2. Specify role, goal, backstory, LLM model, and tools
3. Add agent to workflow crew in `create_workflow_crew()`
4. Create tasks for the agent with description and expected output

### Adding a New CrewAI Tool
1. Create tool function in `backend/tools.py` using `@tool()` decorator
2. Implement with proper error handling and return strings
3. Add tool to relevant agent's `tools` list in `agents.py`
4. Write unit tests in `tests/test_tools.py`

### Modifying Workflow Phases
1. Update `WorkflowPhase` enum in `backend/models.py`
2. Create phase-specific agent and task in `backend/agents.py`
3. Update phase progression logic in workflow orchestrator
4. Update frontend to handle new phase in spec viewer

### Debugging Workflows
```bash
# Enable verbose logging
echo "LOG_LEVEL=DEBUG" >> .env
./start.sh --restart

# Follow agent logs in real-time
./start.sh --logs

# Check database state
docker-compose exec agent sqlite3 /app/data/db.sqlite "SELECT * FROM features;"

# Inspect spec files
docker-compose exec agent cat /projects/<project>/.spec-workflow/specs/<FEAT-ID>/phase-requirements.yaml
```

## Important Constraints

### Claude-Specific
- **Only use Anthropic Claude models** - No OpenAI, Gemini, or other LLMs
- Model selection via environment variables for different roles
- API key required and validated on startup

### Docker Requirements
- All agents run inside containers with `/projects` mount
- Non-root user (UID 1000) for security
- Multi-stage builds for smaller image sizes
- Healthchecks required for service dependencies

### Spec-Driven Workflow
- All phase outputs must be written to YAML spec files
- Specs are first-class artifacts stored in project repositories
- Approval gates can pause workflow between phases
- Each feature gets unique ID in format `FEAT-YYYYMMDD-NNN`

### File Operations
- Agents operate on files via tools (read_file, write_file, edit_file)
- All file paths are relative to `/projects/<project-name>`
- Git operations use subprocess calls (git status, commit, diff)
- Test runners execute via run_tests tool

## Troubleshooting

Common issues and solutions:

**API Key Errors**
- Verify `.env` file has valid `ANTHROPIC_API_KEY=sk-ant-...`
- Restart containers: `./start.sh --restart`

**Container Won't Start**
- Check logs: `docker-compose logs agent`
- Rebuild: `docker-compose down -v && ./start.sh --build`

**WebSocket Connection Failed**
- Check browser console for errors
- Verify both containers are on `claudeforge-net` network
- Ensure no proxy blocking WebSocket upgrade

**Database Locked**
- Restart agent: `docker-compose restart agent`
- If persistent: `docker-compose exec agent rm /app/data/db.sqlite && docker-compose restart agent`

**Projects Not Showing**
- Verify mount: `docker-compose exec agent ls /projects`
- Check `docker-compose.yml` has `~/github:/projects:rw`

See `docs/TROUBLESHOOTING.md` for detailed debugging steps.

## Reference Documentation

- `SPEC.md` - Complete project specification with architecture details
- `docs/QUICKSTART.md` - Getting started guide
- `docs/WORKFLOW.md` - Detailed workflow phase documentation
- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- FastAPI docs: `http://localhost:8000/docs` (auto-generated API documentation)
