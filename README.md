# ClaudeForge

Docker-based, spec-driven AI agent framework for software development workflows. Uses CrewAI with Claude models to implement a six-phase autonomous workflow with human oversight.

## Features

- Six-phase workflow: Requirements → Design → Tasks → Implementation → Verification → Review
- Real-time dashboard with WebSocket log streaming
- Manual approval gates or fully autonomous mode
- CrewAI agents with specialized roles and tools

## Prerequisites

- Docker and Docker Compose
- Anthropic API key

## Quick Start

```bash
# Copy environment template and add your API key
cp .env.example .env

# Build and start
./start.sh --build

# Access dashboard at http://localhost:5050
# API at http://localhost:8000
```

## Usage

```bash
# Inside agent container
claudeforge start myproject "Add user authentication"
claudeforge status
claudeforge approve FEAT-20260130-001 requirements
```

## Development

```bash
# Run backend tests
docker-compose exec agent pytest

# Run frontend checks
docker-compose exec dashboard npm run check
```

## License

MIT
