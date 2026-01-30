# Docker Standards for ClaudeForge

This document defines the Docker standards that agents should enforce when validating Dockerfiles and docker-compose configurations.

## Dockerfile Requirements

### Multi-Stage Builds

All Dockerfiles should use multi-stage builds to minimize final image size:

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
COPY --from=builder /app/dist ./dist
```

### Non-Root User

Containers must run as non-root user for security:

```dockerfile
# Create user
RUN useradd -m -u 1000 appuser

# Switch to non-root
USER appuser
```

### Health Checks

All service containers must include health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Version Pinning

Always pin base image versions - never use `:latest`:

```dockerfile
# Good
FROM python:3.12-slim

# Bad
FROM python:latest
```

### Layer Optimization

Order Dockerfile commands from least to most frequently changing:

```dockerfile
# System dependencies (rarely change)
RUN apt-get update && apt-get install -y ...

# Application dependencies (sometimes change)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code (frequently changes)
COPY . .
```

### Cache Optimization

Leverage Docker's build cache:

```dockerfile
# Good - dependency installation is cached
COPY package*.json ./
RUN npm ci
COPY . .

# Bad - any code change invalidates cache
COPY . .
RUN npm ci
```

## docker-compose Requirements

### Service Naming

Use descriptive, kebab-case service names:

```yaml
services:
  api-server:
  web-frontend:
  job-worker:
```

### Resource Limits

Define memory and CPU limits for production:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

### Restart Policies

Set appropriate restart policies:

```yaml
services:
  api:
    restart: unless-stopped
```

### Network Isolation

Use custom networks for service isolation:

```yaml
networks:
  internal:
    driver: bridge
  external:
    driver: bridge

services:
  api:
    networks:
      - internal
  proxy:
    networks:
      - internal
      - external
```

### Volume Best Practices

Use named volumes for persistent data:

```yaml
volumes:
  db-data:

services:
  database:
    volumes:
      - db-data:/var/lib/postgresql/data
```

### Environment Variables

Never commit secrets - use env files:

```yaml
services:
  api:
    env_file:
      - .env
```

## .dockerignore

Every project should have a `.dockerignore`:

```
# Dependencies
node_modules/
__pycache__/
venv/

# Build output
dist/
build/

# Development
.git/
.env
*.log

# IDE
.vscode/
.idea/
```

## Security Checklist

- [ ] Non-root user
- [ ] No secrets in image
- [ ] Pinned base versions
- [ ] Health checks defined
- [ ] Minimal base image
- [ ] No unnecessary packages
- [ ] Proper file permissions
