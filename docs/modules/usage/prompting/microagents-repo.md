# Repository Microagents

## Overview

OpenHands can be customized to work more effectively with specific repositories by providing repository-specific context
and guidelines. This section explains how to optimize OpenHands for your project.

## Creating a Repository Micro-Agent

You can customize OpenHands' behavior for your repository by creating a `.openhands/microagents/` directory in your repository's root.
At minimum it should contain the file
`.openhands/microagents/repo.md`, which includes instructions that will
be given to the agent every time it works with this repository.

### Repository Microagents Best Practices

- **Keep Instructions Updated**: Regularly update your `.openhands/microagents/` directory as your project evolves.
- **Be Specific**: Include specific paths, patterns, and requirements unique to your project.
- **Document Dependencies**: List all tools and dependencies required for development.
- **Include Examples**: Provide examples of good code patterns from your project.
- **Specify Conventions**: Document naming conventions, file organization, and code style preferences.

### Steps to Create a Repository Microagent

#### 1. Plan the Repository Microagent
When creating a repository-specific micro-agent, we suggest including the following information:
- **Repository Overview**: A brief description of your project's purpose and architecture.
- **Directory Structure**: Key directories and their purposes.
- **Development Guidelines**: Project-specific coding standards and practices.
- **Testing Requirements**: How to run tests and what types of tests are required.
- **Setup Instructions**: Steps needed to build and run the project.

#### 2. Create File

Create a file in your repository under `.openhands/microagents/` (Example: `.openhands/microagents/repo.md`)

Update the file with the required frontmatter [according to the required format](./microagents-overview#microagent-format)
and the required specialized guidelines for your repository.

### Example Repository Microagent

```
---
name: repo
type: repo
agent: CodeActAgent
---

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

If adding a new component in src/components, always add appropriate unit tests in tests/components/.
```
