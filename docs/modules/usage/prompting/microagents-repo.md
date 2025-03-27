# Repository Microagents

## Overview

OpenHands can be customized to work more effectively with specific repositories by providing repository-specific context and guidelines.

This section explains how to optimize OpenHands for your project.

## Creating Repository Microagents

You can customize OpenHands' behavior for your repository by creating a `.openhands/microagents/` directory in your repository's root.

At minimum it should contain the file `.openhands/microagents/repo.md`, which includes instructions that will be given to the agent every time it works with this repository.

## Types of Microagents

OpenHands supports three primary types of microagents, each with specific purposes and features to enhance agent performance:

### Repository Microagents

This microagent type is used to provide general context about the repository:

- Must be located in the `.openhands/microagents/repo.md` file within each individual repository
- Automatically loaded when working on the repository
- Always active for the specific repository

OpenHands does not support multiple `repo.md` files in different locations. Instead, the architecture is designed to have:

- One main `repo.md` file containing repository-specific instructions
- Additional `Knowledge` agents in `.openhands/microagents/knowledge/` directory
- Additional `Task` agents in `.openhands/microagents/tasks/` directory

If you need to organize different types of repository information, the recommended approach is to use a single `repo.md` file with well-structured sections rather than trying to create multiple `Repository` microagents.

The best practice is to include project-specific instructions, team practices, coding standards, and architectural guidelines that are relevant for all prompts in that repository.

Example structure:

```
your-repository/
└── .openhands/
    └── microagents/
        └── repo.md    # Repository-specific instructions
```

### Knowledge Microagents

Knowledge microagents provide specialized domain expertise:

- Must be located in `OpenHands/microagents/knowledge/`
- Triggered by specific keywords in conversations
- Contain expertise on tools, languages, frameworks, and common practices

Use knowledge microagents to trigger additional context relevant to specific technologies, tools, or workflows. For example, mentioning "git" in your conversation will automatically trigger git-related expertise to help with Git operations.

Examples structure:

```
your-repository/
└── .openhands/
    └── microagents/
        └── knowledge/
            └── git.md
            └── docker.md
            └── python.md
            └── ...
        └── repo.md
```

### Task Microagents

Task microagents guide users through interactive workflows:

- Located in `OpenHands/microagents/tasks/`
- Provide step-by-step processes for common development tasks
- Accept inputs and adapt to different scenarios
- Ensure consistent outcomes for complex operations

Task microagents are a convenient way to store multi-step processes you perform regularly. For instance, you can create a `update_pr_description.md` microagent to automatically generate better pull request descriptions based on code changes.

Examples structure:

```
your-repository/
└── .openhands/
    └── microagents/
        └── tasks/
            └── update_pr_description.md
            └── address_pr_comments.md
            └── get_test_to_pass.md
            └── ...
        └── knowledge/
            └── ...
        └── repo.md
```

## Creating Custom Microagents

You can enhance OpenHands' performance by adding custom microagents to your repository:

1. For overall repository-specific instructions, create a `.openhands/microagents/repo.md` file
2. For reusable domain knowledge triggered by keywords, add multiple `.md` files to `.openhands/microagents/knowledge/`
3. For common workflows and tasks, create multiple `.md` files to `.openhands/microagents/tasks/`

When creating microagents, follow these best practices:

- Keep the scope focused and specific
- Include practical examples
- For knowledge agents, choose distinctive triggers
- For task agents, break workflows into clear steps
- For repository agents, document repository structure and team practices

It is important to note that loaded microagents occupy space in the context window. So, it's important to balance well the additional context and the conventional users inputs.

Note that you can use OpenHands to create new microagents. The public microagent [`add_agent`](https://github.com/All-Hands-AI/OpenHands/blob/main/microagents/knowledge/add_agent.md) is loaded to all OpenHands instance and can support you on this.

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
