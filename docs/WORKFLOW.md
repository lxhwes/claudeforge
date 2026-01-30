# ClaudeForge Workflow Documentation

## Overview

ClaudeForge implements a spec-driven development workflow using AI agents. Each feature request progresses through six sequential phases, with optional approval gates between phases.

## Workflow Phases

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Requirements│ → │   Design    │ → │   Tasks     │
└─────────────┘   └─────────────┘   └─────────────┘
                                            │
┌─────────────┐   ┌─────────────┐   ┌───────▼─────┐
│   Review    │ ← │ Verification│ ← │Implementation│
└─────────────┘   └─────────────┘   └─────────────┘
```

### 1. Requirements Phase

**Agent**: Requirements Analyst (Claude Sonnet)

**Purpose**: Gather, clarify, and document comprehensive requirements from the feature description.

**Output**: YAML specification containing:
- Functional requirements
- Non-functional requirements
- User stories/use cases
- Acceptance criteria
- Dependencies and constraints
- Out of scope items

**Example Output**:
```yaml
feature_id: FEAT-20260129-001
phase: requirements
status: pending_approval
content: |
  ## Functional Requirements
  - Users can register with email and password
  - Users can log in and receive a JWT token
  - JWT tokens expire after 24 hours

  ## Non-Functional Requirements
  - Password must be hashed with bcrypt
  - Login response time < 500ms

  ## Acceptance Criteria
  - [ ] User can create account with valid email
  - [ ] User cannot create duplicate accounts
  - [ ] Login returns valid JWT on success
```

### 2. Design Phase

**Agent**: Software Architect (Claude Sonnet)

**Purpose**: Create architectural design based on requirements, considering existing codebase patterns.

**Output**: Design document with:
- High-level architecture overview
- Component diagram (Mermaid format)
- Data models and schemas
- API contracts
- Integration points
- Technology decisions

**Example Output**:
```yaml
content: |
  ## Architecture Overview

  The authentication system will use JWT tokens with refresh capability.

  ## Component Diagram
  ```mermaid
  graph TD
    A[Client] --> B[Auth Controller]
    B --> C[Auth Service]
    C --> D[User Repository]
    D --> E[(Database)]
    C --> F[JWT Util]
  ```

  ## Data Models

  ### User
  - id: UUID
  - email: string (unique)
  - password_hash: string
  - created_at: datetime
```

### 3. Tasks Phase

**Agent**: Task Planner (Claude Sonnet)

**Purpose**: Break down the design into actionable, well-defined development tasks.

**Output**: Task list with:
- Task ID and title
- Description and acceptance criteria
- Files to create or modify
- Dependencies on other tasks
- Complexity estimate
- Test requirements

**Example Output**:
```yaml
content: |
  ## Task Breakdown

  ### TASK-001: Create User Model
  - Files: src/models/user.py
  - Complexity: Low
  - Dependencies: None
  - Tests: Unit tests for model validation

  ### TASK-002: Implement Auth Service
  - Files: src/services/auth.py
  - Complexity: Medium
  - Dependencies: TASK-001
  - Tests: Unit tests for register/login
```

### 4. Implementation Phase

**Agent**: Software Developer (Claude Sonnet)

**Purpose**: Implement the feature according to task specifications.

**Actions**:
- Read existing code for context
- Write or modify code as needed
- Write tests for new functionality
- Commit changes with clear messages

**Tools Available**:
- File read/write/edit
- Git status/commit/diff
- Directory listing
- Code search

### 5. Verification Phase

**Agent**: QA Engineer (Claude Sonnet)

**Purpose**: Verify the implementation through comprehensive testing.

**Actions**:
- Run all tests
- Verify each requirement is met
- Check for edge cases
- Identify bugs or issues

**Output**: Verification report with:
- Test results summary
- Requirement coverage matrix
- Issues found
- Pass/fail status

### 6. Review Phase

**Agent**: Code Reviewer (Claude Haiku)

**Purpose**: Review implementation for quality and provide feedback.

**Focus Areas**:
- Code quality and maintainability
- Adherence to design patterns
- Security considerations
- Performance implications
- Documentation completeness

**Output**: Review report with recommendations.

## Spec File Structure

Each phase generates a YAML file in the project's `.spec-workflow` directory:

```
project/
└── .spec-workflow/
    └── specs/
        └── FEAT-20260129-001/
            ├── phase-requirements.yaml
            ├── phase-design.yaml
            ├── phase-tasks.yaml
            ├── phase-implementation.yaml
            ├── phase-verification.yaml
            └── phase-review.yaml
```

## Status Flow

```
draft → pending_approval → approved → in_progress → completed
                       ↓
                   rejected → (back to draft for revision)
```

## Approval Gates

### Auto-Approve Mode (Default)

Phases automatically advance without human intervention. Useful for:
- Quick prototyping
- Simple features
- Trusted automated flows

### Manual Approval Mode

Set `AUTO_APPROVE=false` to require human approval at each phase. The workflow pauses and waits for:
- Dashboard approval button click
- CLI `claudeforge approve` command
- API POST to `/api/specs/approve`

## Error Handling

### Agent Self-Reflection

When an agent encounters an error:
1. CrewAI's verbose mode logs the error
2. Agent attempts self-reflection to diagnose
3. Retries with adjusted approach
4. If still failing, marks phase as failed

### Recovery Options

- **Retry**: Re-run the failed phase
- **Manual Fix**: Edit spec files directly and resume
- **Reject & Revise**: Reject the phase and provide feedback

## Best Practices

1. **Clear Descriptions**: Provide detailed feature descriptions
2. **Review Requirements**: Always review requirements phase output
3. **Incremental Features**: Break large features into smaller workflows
4. **Monitor Logs**: Watch agent logs for issues
5. **Version Control**: Spec files are git-trackable artifacts
