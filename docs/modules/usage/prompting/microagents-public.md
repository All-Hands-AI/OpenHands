# Public Microagents

## Overview

Public microagents are specialized guidelines triggered by keywords for all OpenHands users.
They are defined in markdown files under the
[`microagents/knowledge/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge) directory.

Public microagents:
- Monitor incoming commands for their trigger words.
- Activate when relevant triggers are detected.
- Apply their specialized knowledge and capabilities.
- Follow their specific guidelines and restrictions.

## Current Public Microagents

For more information about specific microagents, refer to their individual documentation files in
the [`microagents/knowledge/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge/) directory.

### GitHub Agent
**File**: `github.md`
**Triggers**: `github`, `git`

The GitHub agent specializes in GitHub API interactions and repository management. It:
- Has access to a `GITHUB_TOKEN` for API authentication.
- Follows strict guidelines for repository interactions.
- Handles branch management and pull requests.
- Uses the GitHub API instead of web browser interactions.

Key features:
- Branch protection (prevents direct pushes to main/master)
- Automated PR creation
- Git configuration management
- API-first approach for GitHub operations

Usage Example:

```bash
git checkout -b feature-branch
git commit -m "Add new feature"
git push origin feature-branch
```

### NPM Agent
**File**: `npm.md`
**Triggers**: `npm`

Specializes in handling npm package management with specific focus on:
- Non-interactive shell operations.
- Automated confirmation handling using Unix 'yes' command.
- Package installation automation.

Usage Example:

```bash
yes | npm install package-name
```

## Contributing a Public Microagent

You can create your own public microagents by adding new markdown files to the
[`microagents/knowledge/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge/) directory.

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

Create a new markdown file in [`microagents/knowledge/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge/)
with a descriptive name (e.g., `docker.md` for a Docker-focused agent).

Update the file with the required frontmatter [according to the required format](./microagents-overview#microagent-format)
and the required specialized guidelines while following the [best practices above](#public-microagents-best-practices).

#### 3. Testing the Public Microagent

- Test the agent with various prompts.
- Verify trigger words activate the agent correctly.
- Ensure instructions are clear and comprehensive.
- Check for potential conflicts with existing agents.

#### 4. Submission Process

Submit a pull request with:
- The new microagent file.
- Updated documentation if needed.
- Description of the agent's purpose and capabilities.

### Example Public Microagent Implementation

Here's a template for a new microagent:

```markdown
---
name: docker
agent: CodeActAgent
triggers:
- docker
- container
---

You are responsible for Docker container management and Dockerfile creation.

Key responsibilities:
1. Create and modify Dockerfiles
2. Manage container lifecycle
3. Handle Docker Compose configurations

Guidelines:
- Always use official base images when possible
- Include necessary security considerations
- Follow Docker best practices for layer optimization

Examples:
1. Creating a Dockerfile:
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   CMD ["npm", "start"]

2. Docker Compose usage:
   version: '3'
   services:
     web:
       build: .
       ports:
         - "3000:3000"

Remember to:
- Validate Dockerfile syntax
- Check for security vulnerabilities
- Optimize for build time and image size
```

See the [current public micro-agents](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge) for
more examples.
