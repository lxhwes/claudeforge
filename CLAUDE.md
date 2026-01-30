# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClaudeForge is a Docker-based, spec-driven AI agent framework for software development workflows. It uses CrewAI with Anthropic Claude models to implement a six-phase autonomous workflow (Requirements → Design → Tasks → Implementation → Verification → Review) with human oversight via a real-time dashboard.

## Commands

### Docker Operations (Primary)
```bash
./start.sh --build     # Build and start all containers
./start.sh --stop      # Stop all containers
./start.sh --logs      # Follow container logs
./start.sh --shell     # Open bash in agent container
```

### Testing
```bash
# Backend (Python) - via Docker
docker-compose exec agent pytest                           # All tests
docker-compose exec agent pytest tests/test_api.py         # Single file
docker-compose exec agent pytest -k "test_health"          # Single test
docker-compose exec agent pytest --cov=. --cov-report=term # Coverage

# Frontend (SvelteKit) - via Docker
docker-compose exec dashboard npm test                     # Vitest
docker-compose exec dashboard npm run check                # Type checking
docker-compose exec dashboard npm run lint                 # ESLint
```

### Local Development (without Docker)
```bash
# Backend - use uv for Python package management
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install
npm run dev  # Runs on port 5050
```

### CLI (inside agent container)
```bash
claudeforge start <project> "<feature-description>"  # Start workflow
claudeforge status                                    # List running workflows
claudeforge approve <feat_id> <phase>                 # Approve a phase
claudeforge reject <feat_id> <phase> --comment "..."  # Reject a phase
```

## Architecture

### Container Setup
- **agent** (port 8000): Python/FastAPI backend with CrewAI orchestration
- **dashboard** (port 5050): SvelteKit frontend with real-time WebSocket logs
- Communication: REST API + WebSocket (`/ws/logs/{feat_id}`)
- Storage: SQLite at `/app/data/db.sqlite`, projects mounted at `/projects` (maps to `~/code` on host)

### Six-Phase Workflow
Each feature creates YAML spec files in `<project>/.spec-workflow/specs/<FEAT-ID>/`:
1. **Requirements** → Requirements Analyst (Sonnet)
2. **Design** → Software Architect (Sonnet)
3. **Tasks** → Task Planner (Sonnet)
4. **Implementation** → Software Developer (Sonnet)
5. **Verification** → QA Engineer (Sonnet)
6. **Review** → Code Reviewer (Haiku)

The Orchestrator (Opus) coordinates phase transitions. Set `AUTO_APPROVE=true` for one-shot execution without manual approval gates.

### Backend (`backend/`)
- `main.py` - FastAPI app with REST/WebSocket endpoints
- `agents.py` - CrewAI agent definitions, `WorkflowManager`, `run_workflow()`
- `tools.py` - CrewAI tools: file I/O, git operations, test runner
- `models.py` - Pydantic models (Project, Feature, SpecPhase, PhaseStatus, WorkflowPhase)
- `db.py` - SQLite operations via raw SQL
- `utils.py` - Spec file I/O, feature ID generation (`FEAT-YYYYMMDD-NNN`)
- `cli.py` - Typer CLI for workflow management

### Frontend (`frontend/src/`)
- `routes/+page.svelte` - Home: project list
- `routes/projects/[slug]/` - Project spec browser
- `routes/specs/[feat_id]/` - Spec viewer with approval modal
- `routes/agents/` - Real-time agent monitor with WebSocket logs
- `lib/stores/` - API client and WebSocket stores (Svelte writable stores)

## Key Patterns

### Feature ID Format
`FEAT-YYYYMMDD-NNN` (e.g., `FEAT-20260130-001`) - generated in `utils.py:generate_feat_id()`

### Spec File Structure
```
/projects/<project>/.spec-workflow/specs/<FEAT-ID>/
├── phase-requirements.yaml
├── phase-design.yaml
├── phase-tasks.yaml
├── phase-implementation.yaml
├── phase-verification.yaml
└── phase-review.yaml
```

### Agent Tool Registration
Tools in `tools.py` use `@tool` decorator from CrewAI. Each agent has specific tools assigned in `agents.py`.

## Environment Variables

Required in `.env` (copy from `.env.example`):
- `ANTHROPIC_API_KEY` - Claude API key (required)
- `CLAUDE_MODEL_OPUS`, `CLAUDE_MODEL_SONNET`, `CLAUDE_MODEL_HAIKU` - Model selection
- `AUTO_APPROVE` - Skip manual approval gates (default: true)
