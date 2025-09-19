# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

OpenHands is a platform for AI software development agents that can modify code, run commands, browse the web, and perform complex software development tasks. The project consists of a Python backend (`openhands/`) and a React frontend (`frontend/`).

## Essential Development Commands

### Initial Setup
```bash
# Build entire project and install dependencies
make build

# Set up configuration (LLM API key, model, workspace)
make setup-config
```

### Development Server
```bash
# Run both frontend and backend servers
make run

# Start backend server only (port 3000)
make start-backend

# Start frontend server only (port 3001)
make start-frontend
```

### Testing and Quality
```bash
# Run all linting (frontend + backend)
make lint

# Run backend linting only
make lint-backend

# Run frontend linting only
make lint-frontend

# Run frontend tests
make test-frontend

# Run specific unit tests
poetry run pytest ./tests/unit/test_*.py

# Run single test file
poetry run pytest tests/unit/path/to/test_file.py

# Run with coverage
cd frontend && npm run test:coverage
```

### Docker Development
```bash
# Develop inside Docker container
make docker-dev

# Run application in Docker
make docker-run
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Development server (mock API)
npm run dev:mock

# Build for production
npm run build

# Lint and fix
npm run lint:fix

# Type checking
npm run typecheck
```

## Architecture Overview

OpenHands follows a client-server architecture with these core components:

### Backend Components (`openhands/`)

**Core Architecture:**
- **Agent**: AI entity that performs software development tasks (main implementation: CodeActAgent)
- **AgentController**: Manages agent lifecycle, state, and interactions
- **Runtime**: Execution environment for agent actions (Docker/Local/Remote)
- **EventStream**: Central communication hub for all system events
- **ActionExecutor**: Executes actions in sandboxed runtime environments

**Key Modules:**
- `openhands/agenthub/`: Different agent implementations
- `openhands/server/`: WebSocket server and API endpoints  
- `openhands/runtime/`: Runtime implementations (Docker, Local, Remote)
- `openhands/events/`: Event system (Actions and Observations)
- `openhands/controller/`: Agent controller and state management

**Event-Driven Flow:**
```
User Input → Frontend → WebSocket → AgentController → Agent → EventStream → Runtime → ActionExecutor
```

### Frontend Components (`frontend/`)

**Technology Stack:**
- React 19.1+ with TypeScript
- React Router for routing
- Redux Toolkit for state management
- TailwindCSS for styling  
- Monaco Editor for code editing
- WebSocket for real-time communication

**Key Features:**
- Real-time chat interface with AI agents
- Integrated terminal and file browser
- Code editor with syntax highlighting
- Multi-language support (i18n)

### Runtime System

OpenHands uses a **client-server runtime architecture**:

1. **Runtime Client** (`openhands/runtime/impl/`): Manages runtime lifecycle
2. **Action Execution Server** (`openhands/runtime/action_execution_server.py`): REST API that executes actions
3. **Docker Container**: Sandboxed environment with bash, Jupyter, and browser tools

**Supported Runtimes:**
- **Docker Runtime**: Local containerized execution (default)
- **Local Runtime**: Direct execution on host machine  
- **Remote Runtime**: Execution on remote servers
- **Modal Runtime**: Cloud-based execution via Modal API

## Development Workflows

### Agent Development
- Main agent: **CodeActAgent** (`openhands/agenthub/codeact_agent/`)
- Modify prompts and behavior in agent-specific directories
- Test changes against SWE-bench benchmark for evaluation
- Use `export DEBUG=1` for LLM prompt/response logging

### Adding New Components

**New Agent:**
```bash
# Create in openhands/agenthub/your_agent/
mkdir openhands/agenthub/your_agent
# Implement agent class inheriting from base Agent
```

**New Runtime:**
```bash
# Implement Runtime interface in openhands/runtime/impl/
# Register in runtime registry
```

### Testing Strategy

**Unit Tests:** Focus on individual components in `tests/unit/`
**Integration Tests:** End-to-end scenarios in `evaluation/integration_tests/`
**Frontend Tests:** Component testing with Vitest and Playwright

### Code Quality
- **Pre-commit hooks**: Automatically installed via `make build`
- **Linting**: Ruff for Python, ESLint for TypeScript  
- **Type checking**: MyPy for Python, TypeScript for frontend
- **Formatting**: Black for Python, Prettier for frontend

## Configuration and Environment

### Environment Variables
```bash
# Backend
LLM_API_KEY=your-api-key
LLM_MODEL=anthropic/claude-sonnet-4-20250514  # Recommended
SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.56-nikolaik

# Development
DEBUG=1  # Enable LLM debugging
INSTALL_DOCKER=0  # Skip Docker dependency checks
RUNTIME=local  # Use local runtime
```

### Key Configuration Files
- `config.toml`: Runtime configuration (created by `make setup-config`)
- `pyproject.toml`: Python dependencies and tool settings
- `frontend/package.json`: Frontend dependencies and scripts

## Common Development Tasks

### Debugging Agent Behavior
1. Set `DEBUG=1` environment variable
2. Check logs in `logs/llm/CURRENT_DATE/` for LLM interactions
3. Use browser dev tools for frontend debugging
4. Monitor EventStream via WebSocket debugging

### Working with Dependencies
```bash
# Add Python dependency
poetry add package-name
poetry lock --no-update

# Add frontend dependency  
cd frontend && npm install package-name
```

### Running Evaluations
```bash
# SWE-bench evaluation (main benchmark)
# See evaluation/benchmarks/swe_bench/README.md

# Custom evaluation
python -m openhands.eval.your_evaluation
```

## Important Notes

- **Python 3.12** required (no Python 3.11 or older)
- **Node.js 22+** required for frontend
- **Docker** required for default runtime (unless using local runtime)
- **Poetry 1.8+** for Python dependency management
- Uses **tmux** for persistent terminal sessions in runtime
- **LiteLLM** powers LLM integration with multiple providers
- **BrowserGym** handles web browsing capabilities

## Repository Structure

```
OpenHands/
├── openhands/           # Python backend
│   ├── agenthub/       # Agent implementations  
│   ├── server/         # API server and WebSocket
│   ├── runtime/        # Runtime implementations
│   ├── events/         # Event system
│   └── controller/     # Agent controller
├── frontend/           # React frontend application
├── evaluation/         # Benchmarking and evaluation
├── microagents/        # Domain-specific agent configurations
├── containers/         # Docker configurations  
├── tests/              # Test suites
└── docs/              # Documentation
```

This architecture enables secure, scalable AI agent execution with real-time web interface and multiple runtime options.