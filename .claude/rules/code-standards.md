# Code Standards for ClaudeForge

This document defines the coding standards that agents should follow when generating or reviewing code.

## General Principles

1. **Readability over cleverness** - Code should be easy to understand
2. **Consistency** - Follow existing patterns in the codebase
3. **Simplicity** - Prefer simple solutions over complex ones
4. **Documentation** - Document the "why", not the "what"

## Python Standards

### Style Guide

Follow PEP 8 with these specifics:

- Line length: 88 characters (Black default)
- Imports: grouped and sorted (isort)
- Quotes: double quotes for strings

### Type Hints

All functions should have type hints:

```python
def process_data(items: list[str], limit: int = 10) -> dict[str, int]:
    """Process items and return counts."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_total(prices: list[float], tax_rate: float) -> float:
    """Calculate total price including tax.

    Args:
        prices: List of item prices.
        tax_rate: Tax rate as decimal (e.g., 0.08 for 8%).

    Returns:
        Total price including tax.

    Raises:
        ValueError: If tax_rate is negative.
    """
```

### Error Handling

Be specific with exceptions:

```python
# Good
try:
    data = load_config(path)
except FileNotFoundError:
    logger.error(f"Config file not found: {path}")
    raise
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config: {e}")
    raise ConfigError(f"Invalid config format: {path}") from e

# Bad
try:
    data = load_config(path)
except:
    pass
```

### Async Patterns

Use async/await consistently:

```python
async def fetch_all(urls: list[str]) -> list[dict]:
    """Fetch all URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_one(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

## TypeScript/JavaScript Standards

### Style Guide

- Use TypeScript for all new code
- Prefer `const` over `let`
- Use arrow functions for callbacks
- Destructure objects and arrays

### Type Safety

```typescript
// Good
interface User {
  id: string;
  name: string;
  email: string;
}

function getUser(id: string): Promise<User> {
  // ...
}

// Bad
function getUser(id: any): any {
  // ...
}
```

### React/Svelte Patterns

Component files should:
- Export a single component
- Use meaningful prop names
- Include prop validation/types

```svelte
<script lang="ts">
  export let title: string;
  export let items: string[] = [];
  export let onSelect: (item: string) => void;
</script>
```

## Testing Standards

### Test Structure

```python
def test_should_describe_expected_behavior():
    """Describe what the test verifies."""
    # Arrange
    user = create_test_user()

    # Act
    result = user.authenticate("password123")

    # Assert
    assert result.success is True
    assert result.token is not None
```

### Test Coverage

- Aim for 80%+ coverage on business logic
- 100% coverage on critical paths
- Don't test implementation details

### Naming Conventions

```python
# Test functions: test_<what>_<condition>_<expected>
def test_login_with_valid_credentials_returns_token():
    ...

def test_login_with_invalid_password_raises_auth_error():
    ...
```

## Git Commit Standards

### Commit Messages

Format: `type(scope): description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `style`: Formatting
- `chore`: Maintenance

Examples:
```
feat(auth): add JWT token refresh endpoint
fix(api): handle null user in profile endpoint
docs(readme): add deployment instructions
```

### Commit Best Practices

- Atomic commits (one logical change)
- Descriptive but concise messages
- Reference issues when relevant
- Don't commit commented-out code

## API Design

### RESTful Conventions

```
GET    /api/users          # List users
POST   /api/users          # Create user
GET    /api/users/{id}     # Get user
PUT    /api/users/{id}     # Update user
DELETE /api/users/{id}     # Delete user
```

### Response Format

```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "total": 100
  }
}
```

### Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid"
    }
  }
}
```

## Security Standards

### Input Validation

- Validate all user input
- Use parameterized queries
- Sanitize output for XSS prevention

### Authentication

- Use secure token storage
- Implement rate limiting
- Hash passwords with bcrypt/argon2

### Secrets Management

- Never commit secrets
- Use environment variables
- Rotate credentials regularly
