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

```
Repository: MyProject
Description: A web application for task management

Directory Structure:
- src/: Main application code
- tests/: Test files
- docs/: Documentation

Setup:
- Run `npm install` to install dependencies
- Use `npm run dev` for development
- Run `npm test` for testing

Guidelines:
- Follow ESLint configuration
- Write tests for all new features
- Use TypeScript for new code
```

### Best Practices

1. **Keep Instructions Updated**: Regularly update the file as your project evolves
2. **Be Specific**: Include specific paths, patterns, and requirements unique to your project
3. **Document Dependencies**: List all tools and dependencies required for development
4. **Include Examples**: Provide examples of good code patterns from your project
5. **Specify Conventions**: Document naming conventions, file organization, and code style preferences

## The `.openhands` Directory

The `.openhands` directory allows you to create repository-specific micro-agents that extend OpenHands' capabilities for your project. These micro-agents are defined in markdown files within this directory.

### Structure

Each micro-agent file in the `.openhands` directory should follow this format:

```markdown
---
name: agent_name
agent: CodeActAgent
triggers:
- trigger_word1
- trigger_word2
---

Instructions and capabilities for the micro-agent...
```

### Example Custom Micro-Agent

Here's an example of a custom micro-agent for a project using a specific testing framework:

```markdown
---
name: custom_test_agent
agent: CodeActAgent
triggers:
- test
- spec
---

You are responsible for managing tests in this project.

Key responsibilities:
1. Create and modify test files following project conventions
2. Ensure proper test coverage
3. Follow testing best practices

Guidelines:
- Place unit tests in `tests/unit/`
- Name test files with `test_` prefix
- Include both positive and negative test cases
- Use the project's testing utilities from `tests/utils/`

Example test structure:
```python
from tests.utils import TestBase

def test_feature_success():
    # Test successful case
    ...

def test_feature_failure():
    # Test error handling
    ...
```

Remember to:
- Run the full test suite before submitting
- Update test documentation when adding new test cases
- Follow the project's assertion style
```

### Best Practices for Custom Micro-Agents

1. **Clear Scope**: Keep each micro-agent focused on a specific domain or task
2. **Explicit Instructions**: Provide clear, unambiguous guidelines
3. **Useful Examples**: Include practical examples of common use cases
4. **Safety First**: Include necessary warnings and constraints
5. **Integration Awareness**: Consider how the agent interacts with other components

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
