# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenHands (formerly OpenDevin) is a platform for AI-powered software development agents. The agents can modify code, run commands, browse the web, call APIs, and interact with development environments through a sandboxed runtime system.

## Common Development Commands

### Build and Setup
- `make build` - Full project build including environment setup and dependencies
- `make setup-config` - Interactive configuration setup for LLM API keys and settings
- `poetry install --with dev,test,runtime` - Install Python dependencies

### Development
- `make run` - Start both backend and frontend servers
- `make start-backend` - Start FastAPI backend server only (`openhands.server.listen:app`)
- `make start-frontend` - Start React frontend development server only
- Backend runs on port 3000, frontend on port 3001 by default

### Testing and Quality
- `poetry run pytest ./tests/unit/test_*.py` - Run unit tests
- `cd frontend && npm run test` - Run frontend tests
- `make lint` - Run linters for both frontend and backend
- `make lint-backend` - Run Python linters (ruff, pre-commit hooks)
- `make lint-frontend` - Run frontend linters (ESLint, Prettier)
- `poetry run ruff check` - Python linting
- `poetry run mypy` - Python type checking

### Single Test Execution
- `poetry run pytest tests/unit/test_specific_file.py::test_function_name` - Run specific test
- `cd frontend && npm run test -- --testNamePattern="test name"` - Run specific frontend test

## Architecture Overview

### Core Components
- **openhands/core/** - Core abstractions, configuration, and schemas
- **openhands/controller/** - Agent orchestration and control logic
- **openhands/agenthub/** - Different agent implementations (CodeAct, Browsing, etc.)
- **openhands/runtime/** - Sandboxed execution environments (Docker, local, remote)
- **openhands/events/** - Event-driven communication system between agents and UI
- **openhands/llm/** - LLM integration layer using LiteLLM for multi-provider support
- **openhands/server/** - FastAPI web server and API routes
- **frontend/** - React/TypeScript UI application

### Key Patterns
1. **Event-Driven Architecture**: All agent communication flows through events in `openhands/events/`
2. **Agent Pattern**: Agents inherit from base classes in `openhands/core/` and implement specific capabilities
3. **Runtime Isolation**: All code execution happens in sandboxed containers for security
4. **State Management**: Agent sessions maintain state through the controller system
5. **Async/Await**: Extensive use of asyncio patterns throughout the codebase

### Data Flow
1. User input comes through frontend or CLI
2. Actions are created and added to the event stream
3. Agent controller processes actions and generates observations
4. Runtime executes commands in sandboxed environment
5. Results flow back through observations to update UI state

## Configuration

### Main Config Files
- `config.toml` - Main application configuration (created by `make setup-config`)
- `pyproject.toml` - Python dependencies and build configuration
- `frontend/package.json` - Frontend dependencies and scripts
- `.cursorrules` - Cursor IDE development guidelines (comprehensive coding standards)

### Environment Variables
- Configuration can be overridden via environment variables
- Priority: Environment variables > config.toml > defaults
- Common: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `SANDBOX_RUNTIME_CONTAINER_IMAGE`

## Development Notes

### Python Requirements
- Python 3.12+ required (strictly maintained)
- Use Poetry for dependency management
- Type hints mandatory - use mypy for checking
- Follow Google docstring convention
- Use ruff for linting and formatting

### Frontend Requirements
- Node.js >= 22.x required
- React/TypeScript with Vite build system
- Uses React Router for navigation
- Tailwind CSS for styling

### Key Development Guidelines
- All code execution must be sandboxed - never run untrusted code directly
- Use async/await patterns for I/O operations
- Implement comprehensive error handling with structured logging
- Write tests for all new functionality
- Follow the event-driven architecture patterns
- Use LiteLLM abstraction for LLM provider integration

### Agent Development
When creating new agents:
1. Inherit from base classes in `openhands/core/`
2. Implement proper event handling
3. Use structured logging for debugging
4. Handle failures gracefully with retries
5. Add comprehensive tests

### Testing Strategy
- Unit tests in `tests/unit/` using pytest
- Frontend tests using Vitest
- Integration tests in `tests/runtime/`
- Mock external dependencies (LLM calls, network requests)
- Test both success and failure scenarios