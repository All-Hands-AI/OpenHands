---
sidebar_position: 9
---

# Development Overview

This guide provides an overview of the key documentation resources available in the OpenHands repository. Whether you're looking to contribute, understand the architecture, or work on specific components, these resources will help you navigate the codebase effectively.

## Core Documentation

### Project Fundamentals
- **Main Project Overview** (`/README.md`)
  The primary entry point for understanding OpenHands, including features and basic setup instructions.

- **Development Guide** (`/Development.md`)
  Comprehensive guide for developers working on OpenHands, including setup, requirements, and development workflows.

- **Contributing Guidelines** (`/CONTRIBUTING.md`)
  Essential information for contributors, covering code style, PR process, and contribution workflows.

### Component Documentation

#### Frontend
- **Frontend Application** (`/frontend/README.md`)
  Complete guide for setting up and developing the React-based frontend application.

#### Backend
- **Backend Implementation** (`/openhands/README.md`)
  Detailed documentation of the Python backend implementation and architecture.

- **Server Documentation** (`/openhands/server/README.md`)
  Server implementation details, API documentation, and service architecture.

- **Runtime Environment** (`/openhands/runtime/README.md`)
  Documentation covering the runtime environment, execution model, and runtime configurations.

#### Infrastructure
- **Container Documentation** (`/containers/README.md`)
  Comprehensive information about Docker containers, deployment strategies, and container management.

### Testing and Evaluation
- **Unit Testing Guide** (`/tests/unit/README.md`)
  Instructions for writing, running, and maintaining unit tests.

- **Evaluation Framework** (`/evaluation/README.md`)
  Documentation for the evaluation framework, benchmarks, and performance testing.

### Advanced Features
- **Microagents Architecture** (`/microagents/README.md`)
  Detailed information about the microagents architecture, implementation, and usage.

### Documentation Standards
- **Documentation Style Guide** (`/docs/DOC_STYLE_GUIDE.md`)
  Standards and guidelines for writing and maintaining project documentation.

## Getting Started with Development

If you're new to developing with OpenHands, we recommend following this sequence:

1. Start with the main `README.md` to understand the project's purpose and features
2. Review the `CONTRIBUTING.md` guidelines if you plan to contribute
3. Follow the setup instructions in `Development.md`
4. Dive into specific component documentation based on your area of interest:
   - Frontend developers should focus on `/frontend/README.md`
   - Backend developers should start with `/openhands/README.md`
   - Infrastructure work should begin with `/containers/README.md`

## Documentation Updates

When making changes to the codebase, please ensure that:
1. Relevant documentation is updated to reflect your changes
2. New features are documented in the appropriate README files
3. Any API changes are reflected in the server documentation
4. Documentation follows the style guide in `/docs/DOC_STYLE_GUIDE.md`
