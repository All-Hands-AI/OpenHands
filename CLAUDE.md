# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key Commands

### Environment Setup
```bash
# Install dependencies
make build

# Configure LLM settings (required for running agents)
make setup-config

# Install pre-commit hooks
make install-pre-commit-hooks
```

### Database Setup
```bash
# Ensure .env exists
[ ! -f .env ] && cp .env.example .env

# Start PostgreSQL container
docker-compose up -d postgres
```

### Running the Application
```bash
# Run backend only
make start-backend
```

### Testing
```bash
# Run Python unit tests
poetry run pytest ./tests/unit/test_*.py

```

### Code Quality
```bash
# Lint entire project
make lint

# Lint backend only (Python)
make lint-backend

# Auto-fix linting issues
cd frontend && npm run lint:fix
```

### Docker Development
```bash
# Build and run in Docker container
make docker-dev

# Run application in Docker
make docker-run
```

## High-Level Architecture

### Core Components

**Backend (Python/FastAPI)**
- `openhands/core/`: Core system components
  - `main.py`: Entry point for running agents via command line
  - `config/`: Configuration management (AppConfig, LLMConfig, etc.)
  - `schema/`: Core data models (Action, Observation, Agent)
- `openhands/controller/`: Agent execution control
  - `agent.py`: Base Agent class
  - `agent_controller.py`: Main execution loop
  - `state/`: Agent state management
- `openhands/agenthub/`: Built-in agent implementations
- `openhands/runtime/`: Execution environments (Docker, Local, Remote)
- `openhands/server/`: HTTP API server
  - `session/`: WebSocket session management
  - `routes/`: REST endpoints
- `openhands/events/`: Event system (Actions and Observations)
- `openhands/llm/`: LLM integration layer (uses LiteLLM)

**Frontend (React/TypeScript)**
- Remix SPA with Vite
- Redux for state management
- WebSocket for real-time communication
- Mock Service Worker (MSW) for development

### Key Architectural Patterns

1. **Event-Driven Architecture**: All agent interactions flow through an EventStream as Actions and Observations
2. **Plugin System**: Agents, runtimes, and tools are pluggable components
3. **State Management**: Immutable state updates with full history tracking
4. **Async-First**: Core operations use asyncio for concurrent execution

### Agent Execution Flow
```
User Input → Action → AgentController → Agent → LLM
                ↓                         ↓
            EventStream ← Observation ← Runtime
```

## Development Guidelines

### Python Code Style
- Python 3.12 required
- Ruff for linting (config: `dev_config/python/ruff.toml`)
- MyPy for type checking (config: `dev_config/python/mypy.ini`)
- Single quotes for strings, double quotes for docstrings
- Pre-commit hooks enforce standards

### Frontend Code Style
- TypeScript with strict mode
- ESLint + Prettier for formatting
- React Testing Library for component tests
- Follow existing component patterns in `frontend/src/components/`

### Testing Requirements
- Unit tests for new Python modules in `tests/unit/`
- Frontend component tests in `frontend/__tests__/`
- Integration tests for agent behaviors in `tests/integration/`

## Important Configuration

### Environment Variables
- `RUN_MODE=DEV`: Bypass user authentication in development
- `DEBUG=1`: Enable LLM prompt/response logging
- `SANDBOX_RUNTIME_CONTAINER_IMAGE`: Use existing Docker image for runtime

### Database
- PostgreSQL required for session storage
- Configured via `.env` file (copy from `.env.example`)

### LLM Configuration
- Default model: Claude 3.5 Sonnet (`anthropic/claude-3-5-sonnet-20241022`)
- Configure via `make setup-config` or `config.toml`
- Supports any LiteLLM-compatible model

## Common Development Tasks

### Adding a New Agent
1. Create agent class in `openhands/agenthub/your_agent/`
2. Inherit from `openhands.controller.agent.Agent`
3. Implement `step()` method
4. Register in `openhands/agenthub/__init__.py`

### Modifying the Frontend
1. Components go in `frontend/src/components/`
2. API calls in `frontend/src/api/`
3. State management in `frontend/src/state/`
4. Run `npm run dev:mock` for development with mocked backend

### Working with Events
- Actions: User/agent requests (in `openhands/events/action/`)
- Observations: System responses (in `openhands/events/observation/`)
- All events must be serializable and inherit from base Event class