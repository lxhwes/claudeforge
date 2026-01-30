# ClaudeForge Quick Start Guide

Get started with ClaudeForge in minutes!

## Prerequisites

- Docker and Docker Compose installed
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Projects to work with in `~/github/` directory

## Setup

### 1. Clone and Configure

```bash
# Navigate to the project
cd ~/github/claudeforge

# Copy environment template
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 2. Start ClaudeForge

```bash
# Build and start containers
./start.sh --build
```

This will:
- Build the agent container (Python backend with CrewAI)
- Build the dashboard container (SvelteKit frontend)
- Start both containers with proper networking

### 3. Access the Dashboard

Open your browser to: **http://localhost:5050**

You should see the ClaudeForge dashboard with your mounted projects listed.

## Starting Your First Workflow

### Via Dashboard

1. Click "New Workflow" on the Projects page
2. Select a project from the dropdown
3. Enter a feature description (e.g., "Add user authentication with JWT")
4. Click "Start Workflow"

### Via CLI

```bash
# Enter the agent container
docker exec -it claudeforge-agent bash

# Start a workflow
claudeforge start sample-project "Add user authentication with JWT"

# Check status
claudeforge status FEAT-YYYYMMDD-NNN
```

## Workflow Phases

Each feature goes through six phases:

1. **Requirements** - Analyst agent gathers and clarifies requirements
2. **Design** - Architect agent creates technical design
3. **Tasks** - Planner agent breaks down into implementation tasks
4. **Implementation** - Developer agent writes and commits code
5. **Verification** - QA agent runs tests and validates
6. **Review** - Reviewer agent provides feedback

### Approval Gates

By default, workflows auto-approve phases for one-shot execution. To enable manual approval:

```bash
# Set AUTO_APPROVE=false in your environment
AUTO_APPROVE=false ./start.sh
```

## Common Commands

```bash
# Start containers
./start.sh

# Build and start
./start.sh --build

# Stop containers
./start.sh --stop

# View logs
./start.sh --logs

# Check status
./start.sh --status

# Open shell in agent container
./start.sh --shell
```

## Inside the Agent Container

```bash
# List projects
claudeforge projects

# Start a workflow
claudeforge start <project> "feature description"

# Check workflow status
claudeforge status <feat-id>

# View logs
claudeforge logs <feat-id>

# Approve a phase
claudeforge approve <feat-id> requirements -c "Looks good!"

# Verify health
claudeforge verify
```

## API Endpoints

The API is available at **http://localhost:8000**:

- `GET /health` - Health check
- `GET /api/projects/list` - List projects
- `POST /api/agents/start` - Start workflow
- `GET /api/agents/status/{feat_id}` - Get workflow status
- `GET /api/specs/{project}/{feat_id}` - Get spec data
- `POST /api/specs/approve` - Approve/reject phase

## Troubleshooting

### API Key Issues

```
Error: ANTHROPIC_API_KEY not set
```

Make sure your `.env` file has a valid API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Container Won't Start

```bash
# Check logs
docker-compose logs agent

# Rebuild from scratch
docker-compose down -v
./start.sh --build
```

### WebSocket Connection Failed

The dashboard uses WebSockets for real-time logs. If you're behind a proxy, ensure WebSocket upgrade is allowed.

## Next Steps

- Read [WORKFLOW.md](./WORKFLOW.md) for detailed workflow documentation
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
- Explore the API at http://localhost:8000/docs
