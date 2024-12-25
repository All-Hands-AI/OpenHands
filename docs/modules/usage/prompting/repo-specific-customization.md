# Repository-Specific Prompt Customization

OpenHands provides two powerful ways to customize its behavior for specific repositories:

1. `.openhands_instructions` file for repository-wide guidelines
2. `.openhands` directory for custom micro-agents

## The `.openhands_instructions` File

The `.openhands_instructions` file is a simple text file placed in the root directory of your repository that provides repository-specific context and guidelines to OpenHands. This file's contents are automatically injected into the prompt when OpenHands processes issues or pull requests.

### What to Include

Your `.openhands_instructions` file should contain:

1. **Repository Overview**: A brief description of your project's purpose and architecture
2. **Directory Structure**: Key directories and their purposes
3. **Development Guidelines**: Project-specific coding standards and practices
4. **Testing Requirements**: How to run tests and what types of tests are required
5. **Setup Instructions**: Steps needed to build and run the project

### Example `.openhands_instructions` File

Your `.openhands_instructions` file can contain information like the following:

```
This repository is a Python package that provides utilities for data processing.

Key directories:
- src/data_utils/: Core data processing modules
- tests/: Test files organized by module
- docs/: API documentation and usage guides

Development setup:
1. Create a virtual environment: python -m venv venv
2. Activate: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)
3. Install dev dependencies: pip install -e ".[dev]"

Code guidelines:
- Follow PEP 8 style guide
- All new code must have type hints
- Maintain 90% test coverage for new features
- Document public APIs using Google docstring format

Testing:
- Run tests: pytest tests/
- Run type checks: mypy src/
- Run linting: flake8 src/

Common gotchas:
- The data_loader module requires pandas>=2.0
- Test data files must be placed in tests/fixtures/
- Large data operations should use chunked processing
```

### Best Practices

1. **Keep Instructions Updated**: Regularly update the file as your project evolves
2. **Be Specific**: Include specific paths, patterns, and requirements unique to your project
3. **Document Dependencies**: List all tools and dependencies required for development
4. **Include Examples**: Provide examples of good code patterns from your project
5. **Specify Conventions**: Document naming conventions, file organization, and code style preferences

## The `.openhands` Directory

The `.openhands` directory allows you to create repository-specific micro-agents that extend OpenHands' capabilities for your project. For detailed information about creating and using micro-agents, please refer to the [Micro-Agents documentation](../micro-agents.md).

## Using Both Features Together

The `.openhands_instructions` file and `.openhands` directory complement each other:

- Use `.openhands_instructions` for repository-wide guidelines and context
- Use `.openhands` directory for specialized, task-specific agents

For example:
1. `.openhands_instructions` defines your project's overall structure and standards
2. Custom micro-agents in `.openhands` handle specific tasks like testing, deployment, or domain-specific operations

This combination allows OpenHands to:
- Understand your project's context and requirements (via `.openhands_instructions`)
- Handle specialized tasks effectively (via custom micro-agents)
- Maintain consistency with your project's standards
- Automate repository-specific workflows
