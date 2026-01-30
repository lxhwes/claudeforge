# ClaudeForge Troubleshooting Guide

## Common Issues and Solutions

### API Key Issues

#### Error: ANTHROPIC_API_KEY not set

**Symptom**: Container fails to start or agents don't run.

**Solution**:
1. Ensure `.env` file exists in the project root
2. Verify the API key format: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. Restart containers: `./start.sh --restart`

#### Error: Invalid API key

**Symptom**: Agents fail with authentication errors.

**Solution**:
1. Verify your API key at [console.anthropic.com](https://console.anthropic.com/)
2. Check for extra whitespace in `.env` file
3. Ensure the key has proper permissions

### Container Issues

#### Containers won't start

**Symptom**: `docker-compose up` fails or containers exit immediately.

**Solutions**:

1. Check Docker is running:
   ```bash
   docker info
   ```

2. View container logs:
   ```bash
   docker-compose logs agent
   docker-compose logs dashboard
   ```

3. Rebuild from scratch:
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   ./start.sh --build
   ```

#### Health check failing

**Symptom**: Container reports unhealthy status.

**Solutions**:

1. Check if the API is responding:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check container logs for errors:
   ```bash
   docker-compose logs agent | tail -50
   ```

3. Verify port availability:
   ```bash
   lsof -i :8000
   lsof -i :5050
   ```

### Network Issues

#### Dashboard can't connect to API

**Symptom**: Dashboard shows connection errors.

**Solutions**:

1. Verify both containers are on the same network:
   ```bash
   docker network inspect claudeforge_claudeforge-net
   ```

2. Check internal connectivity:
   ```bash
   docker-compose exec dashboard wget -qO- http://agent:8000/health
   ```

3. Restart with fresh network:
   ```bash
   docker-compose down
   docker network prune
   ./start.sh --build
   ```

#### WebSocket connection failed

**Symptom**: Real-time logs don't update.

**Solutions**:

1. Check browser console for WebSocket errors
2. Verify WebSocket endpoint is accessible:
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws/logs/test
   ```

3. If behind a proxy, ensure WebSocket upgrade is allowed

### Database Issues

#### SQLite database locked

**Symptom**: Operations fail with "database is locked".

**Solutions**:

1. Restart the agent container:
   ```bash
   docker-compose restart agent
   ```

2. Clear the database (warning: loses data):
   ```bash
   docker-compose exec agent rm /app/data/db.sqlite
   docker-compose restart agent
   ```

### Agent Issues

#### Agents not progressing

**Symptom**: Workflow stuck on a phase.

**Solutions**:

1. Check agent logs:
   ```bash
   claudeforge logs FEAT-ID -n 100
   ```

2. Verify API key has sufficient quota

3. Check for rate limiting in logs

#### Agent errors

**Symptom**: Phase fails with error.

**Solutions**:

1. Check the specific error in logs
2. Retry the workflow:
   ```bash
   # Start a new workflow with same description
   claudeforge start project "same feature description"
   ```

3. If persistent, check Claude API status

### Project Issues

#### Projects not showing

**Symptom**: No projects listed in dashboard.

**Solutions**:

1. Verify mount is correct:
   ```bash
   docker-compose exec agent ls /projects
   ```

2. Check docker-compose.yml volume mount:
   ```yaml
   volumes:
     - ~/github:/projects:rw
   ```

3. Ensure projects exist at mount source:
   ```bash
   ls ~/github
   ```

#### Permission denied on project files

**Symptom**: Can't read/write project files.

**Solutions**:

1. Check file permissions:
   ```bash
   ls -la ~/github/your-project
   ```

2. Container runs as user 1000, ensure files are accessible:
   ```bash
   chown -R 1000:1000 ~/github/your-project
   ```

### Performance Issues

#### Slow phase execution

**Symptom**: Phases take very long to complete.

**Possible Causes**:
- Large codebase being analyzed
- Complex feature description
- API rate limiting

**Solutions**:

1. Break feature into smaller pieces
2. Check API rate limits in Anthropic console
3. Monitor with verbose logging

#### High memory usage

**Symptom**: Containers using excessive memory.

**Solutions**:

1. Set memory limits in docker-compose.yml:
   ```yaml
   services:
     agent:
       mem_limit: 2g
   ```

2. Reduce concurrent operations

## Getting Help

### Collecting Debug Information

When reporting issues, include:

1. Container logs:
   ```bash
   docker-compose logs > debug-logs.txt
   ```

2. Health check output:
   ```bash
   curl http://localhost:8000/health > health.json
   ```

3. Environment (without API key):
   ```bash
   grep -v API_KEY .env
   ```

4. Docker version:
   ```bash
   docker version
   docker-compose version
   ```

### Log Levels

Increase logging verbosity:

```bash
# In .env
LOG_LEVEL=DEBUG
```

Then restart containers.

### Support Channels

- GitHub Issues: Report bugs and feature requests
- Documentation: Check docs/ for detailed guides
