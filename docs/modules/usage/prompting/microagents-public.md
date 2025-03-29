# Public Microagents

## Overview

Public microagents provide specialized context and capabilities for all OpenHands users, regardless of their repository configuration. Unlike repository-specific microagents, public microagents are globally available across all repositories.

Public microagents come in two types:

- **Knowledge microagents**: Automatically activated when keywords in conversations match their triggers
- **Task microagents**: Explicitly invoked by users to guide through specific workflows

Both types follow the same syntax and structure as repository-specific microagents, using markdown files with YAML frontmatter that define their behavior and capabilities. They are located in the official OpenHands repository under:

- [`microagents/knowledge/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge) for knowledge microagents
- [`microagents/tasks/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/tasks) for task microagents

Public microagents:

- Monitor incoming commands for their trigger words.
- Activate when relevant triggers are detected.
- Apply their specialized knowledge and capabilities.
- Follow their specific guidelines and restrictions.

When loading public microagents, OpenHands scans the official repository's microagents directories recursively, processing all markdown files except README.md. The system categorizes each microagent based on its `type` field in the YAML frontmatter, regardless of its exact file location within the knowledge or tasks directories.

## Contributing a Public Microagent

You can create public microagents and share with the community by opening a pull request to the official repository.

See the [CONTRIBUTING.md](https://github.com/All-Hands-AI/OpenHands/blob/main/CONTRIBUTING.md) for specific instructions on how to contribute to OpenHands.

### Public Microagents Best Practices

- **Clear Scope**: Keep the microagent focused on a specific domain or task.
- **Explicit Instructions**: Provide clear, unambiguous guidelines.
- **Useful Examples**: Include practical examples of common use cases.
- **Safety First**: Include necessary warnings and constraints.
- **Integration Awareness**: Consider how the microagent interacts with other components.

### Steps to Contribute a Public Microagent

#### 1. Plan the Public Microagent

Before creating a public microagent, consider:

- What specific problem or use case will it address?
- What unique capabilities or knowledge should it have?
- What trigger words make sense for activating it?
- What constraints or guidelines should it follow?

#### 2. Create File

Create a new Markdown file with a descriptive name in the appropriate directory:

- [`microagents/knowledge/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge) for knowledge microagents
- [`microagents/tasks/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/tasks) for task microagents

Ensure it follows the correct [syntax](./microagents-syntax.md) and [best practices](./microagents-syntax.md#markdown-content-best-practices).

#### 3. Testing the Public Microagent

- Test the agent with various prompts
- Verify trigger words activate the agent correctly
- Ensure instructions are clear and comprehensive
- Check for potential conflicts and overlaps with existing agents

#### 4. Submission Process

Submit a pull request with:

- The new microagent file
- Updated documentation if needed
- Description of the agent's purpose and capabilities
