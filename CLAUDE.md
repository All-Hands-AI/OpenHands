# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenHands (formerly OpenDevin) is a platform for AI-powered software development agents that can modify code, run commands, browse the web, call APIs, and interact with development environments. The project uses an event-driven architecture with sandboxed execution environments for security.

## Essential Commands

### Development Setup
```bash
# Initial setup (installs dependencies, sets up environment)
make build

# Configure LLM settings interactively
make setup-config

# Start full application (backend + frontend)
make run

# Start components individually
make start-backend    # Backend only on localhost:3000
make start-frontend   # Frontend only on localhost:3001
```

### Testing and Quality
```bash
# Run all tests
make test

# Frontend tests only
make test-frontend

# Python unit tests
poetry run pytest ./tests/unit/test_*.py

# Run linting
make lint                # Both frontend and backend
make lint-frontend      # Frontend only (ESLint + Prettier)
make lint-backend       # Backend only (ruff + mypy)
```

### Frontend Development
```bash
cd frontend
npm run dev             # Development server
npm run build           # Production build
npm run typecheck       # TypeScript checking
npm run lint:fix        # Fix linting issues
npm run test:e2e        # Playwright E2E tests
```

### Backend Development
```bash
# Install/update Python dependencies
poetry install --with dev,test,runtime

# Run specific test files
poetry run pytest tests/unit/test_specific_file.py

# Type checking
poetry run mypy openhands/

# Code formatting
poetry run ruff check
poetry run ruff format
```

## High-Level Architecture

### Core Components

**Event-Driven Architecture**: The system revolves around an EventStream that manages Actions (requests) and Observations (responses). All components communicate through events.

**Agent System** (`openhands/agenthub/`):
- **CodeActAgent**: Primary agent implementing the CodeAct paradigm
- **BrowsingAgent**: Web browsing capabilities
- **ReadonlyAgent**: Read-only operations and analysis
- **VisualBrowsingAgent**: Visual web interactions

**Controller** (`openhands/controller/`):
- **AgentController**: Main orchestrator managing agent lifecycle and state
- **State Management**: Tracks agent state, conversation history, execution context
- **Action Parser**: Converts LLM outputs into executable actions

**Runtime Environments** (`openhands/runtime/`):
- **Docker Runtime**: Primary containerized execution (default)
- **Local Runtime**: Direct system execution
- **Remote Runtime**: Distributed execution capabilities
- **Kubernetes Runtime**: Container orchestration support

**LLM Integration** (`openhands/llm/`):
- Uses LiteLLM for multi-provider support (Anthropic, OpenAI, etc.)
- Supports function calling and streaming responses
- Includes metrics and performance tracking

**Memory System** (`openhands/memory/`):
- **ConversationMemory**: Manages dialogue history
- **Condensers**: Context compression for token limits
- **Memory Views**: Different perspectives on conversation history

### Frontend Architecture

**Technology Stack**:
- React with Remix SPA mode and TypeScript
- Redux + TanStack Query for state management
- Tailwind CSS for styling
- WebSocket for real-time communication

**Key Features**:
- Multi-tab interface (Terminal, Browser, Code Editor, Jupyter)
- Real-time updates via WebSocket
- GitHub OAuth integration (SaaS mode)
- i18next for internationalization

### Microagents System

**Microagents** (`microagents/`): Specialized knowledge injection system
- **Repository agents**: Project-specific guidelines (`.openhands/microagents/repo.md`)
- **Keyword agents**: Domain expertise (Git, Docker, testing) triggered by keywords
- **Public agents**: Shared across all users
- **Private agents**: Repository-specific instructions

## Important Development Patterns

### Python Code Standards
- **Type hints mandatory**: Use mypy for type checking
- **Async patterns**: Use async/await for I/O operations
- **Error handling**: Comprehensive error handling with structured logging
- **Pydantic models**: For data validation and serialization
- **Google docstring convention**: For documentation

### Security Considerations
- **Sandbox all execution**: Never run untrusted code outside containers
- **API key management**: Use environment variables, never hardcode
- **Input validation**: Validate all inputs, especially from agents
- **Network security**: Be mindful of network access from sandboxed environments

### Testing Approach
- Write tests for all new functionality
- Use pytest with async support
- Mock external dependencies (LLM calls, network requests)
- Include integration tests for agent workflows
- Frontend tests use Vitest and React Testing Library

## Key File Locations

### Configuration
- `config.toml` - Main application configuration
- `pyproject.toml` - Python dependencies and tool configuration
- `frontend/package.json` - Frontend dependencies and scripts
- `Makefile` - Build automation and common tasks

### Core Implementation
- `openhands/core/` - Core abstractions and schemas
- `openhands/controller/agent_controller.py` - Main agent orchestration
- `openhands/agenthub/codeact_agent/` - Primary agent implementation
- `openhands/events/` - Event system backbone
- `openhands/server/` - FastAPI web server and WebSocket handling

### Frontend Structure
- `frontend/src/routes/` - React Router routes
- `frontend/src/components/` - Reusable React components
- `frontend/src/state/` - Redux state management
- `frontend/src/services/` - API communication and business logic

## Common Development Workflows

### Adding New Agent Types
1. Create new agent in `openhands/agenthub/`
2. Inherit from appropriate base classes in `openhands/core/`
3. Implement proper event handling
4. Add comprehensive tests
5. Update agent registry

### Extending Runtime Capabilities
1. Implement runtime interface in `openhands/runtime/`
2. Add configuration options
3. Update runtime factory
4. Test in sandboxed environment

### Adding New Evaluation Benchmarks
1. Create new benchmark in `evaluation/benchmarks/`
2. Follow standard `run_infer.py` pattern
3. Add configuration and documentation
4. Integrate with evaluation framework

## Environment Variables

Common environment variables for development:
- `LOG_ALL_EVENTS=true` - Enable comprehensive event logging
- `DEBUG=1` - Enable debug mode with detailed LLM logs
- `SANDBOX_RUNTIME_CONTAINER_IMAGE` - Override default runtime image
- `RUNTIME` - Set runtime type (docker, local, remote, kubernetes)

## Troubleshooting

### Common Issues
- **Port conflicts**: Backend runs on 3000, frontend on 3001
- **Docker issues**: Ensure Docker is running and accessible
- **Node version**: Requires Node.js 22.x or later
- **Python version**: Strictly requires Python 3.12
- **Poetry issues**: Ensure Poetry 1.8+ is installed

### Debug Logging
- Backend logs in `logs/` directory
- LLM interaction logs in `logs/llm/CURRENT_DATE/`
- Frontend console for WebSocket and state issues

## Key Dependencies

### Backend
- FastAPI for web framework
- LiteLLM for LLM integration
- Docker for containerization
- Pydantic for data validation
- OpenTelemetry for monitoring

### Frontend
- React 19+ with TypeScript
- Redux Toolkit + TanStack Query
- Tailwind CSS for styling
- Socket.io for WebSocket communication
- Monaco Editor for code editing

This architecture enables secure, scalable AI agent development with comprehensive evaluation capabilities and a modern web interface.