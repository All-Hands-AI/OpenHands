# Public Micro-Agents

OpenHands uses specialized micro-agents to handle specific tasks and contexts efficiently. These micro-agents are small,
focused components that provide specialized behavior and knowledge for particular scenarios.

## Overview

Public micro-agents are defined in markdown files under the
[`microagents/knowledge/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge) directory.
Each micro-agent is configured with:

- A unique name.
- The agent type (typically CodeActAgent).
- Trigger keywords that activate the agent.
- Specific instructions and capabilities.

### Integration

Public micro-agents are automatically integrated into OpenHands' workflow. They:
- Monitor incoming commands for their trigger words.
- Activate when relevant triggers are detected.
- Apply their specialized knowledge and capabilities.
- Follow their specific guidelines and restrictions.

## Available Public Micro-Agents

For more information about specific micro-agents, refer to their individual documentation files in
the [`micro-agents`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents) directory.

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

### Custom Public Micro-Agents

You can create your own public micro-agents by adding new markdown files to the `microagents/knowledge/` directory.
Each file should follow this structure:

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

## Working With Public Micro-Agents

When working with public micro-agents:
- **Use Appropriate Triggers**: Ensure your commands include the relevant trigger words to activate the correct micro-agent.
- **Follow Agent Guidelines**: Each agent has specific instructions and limitations. Respect these for optimal results.
- **API-First Approach**: When available, use API endpoints rather than web interfaces.
- **Automation Friendly**: Design commands that work well in non-interactive environments.

## Contributing a Public Micro-Agent

Best practices for creating public micro-agents:

- **Clear Scope**: Keep the micro-agent focused on a specific domain or task.
- **Explicit Instructions**: Provide clear, unambiguous guidelines.
- **Useful Examples**: Include practical examples of common use cases.
- **Safety First**: Include necessary warnings and constraints.
- **Integration Awareness**: Consider how the micro-agent interacts with other components.

To contribute a new micro-agent to OpenHands:

### 1. Plan the Public Micro-Agent

Before creating a public micro-agent, consider:
- What specific problem or use case will it address?
- What unique capabilities or knowledge should it have?
- What trigger words make sense for activating it?
- What constraints or guidelines should it follow?

### 2. File Structure

Create a new markdown file in `microagents/knowledge/` with a descriptive name (e.g., `docker.md` for a Docker-focused agent).

### 3. Required Components

The micro-agent file must include:

- **Front Matter**: YAML metadata at the start of the file:
```markdown
---
name: your_agent_name
agent: CodeActAgent
triggers:
- trigger_word1
- trigger_word2
---
```

- **Instructions**: Clear, specific guidelines for the agent's behavior:
```markdown
You are responsible for [specific task/domain].

Key responsibilities:
1. [Responsibility 1]
2. [Responsibility 2]

Guidelines:
- [Guideline 1]
- [Guideline 2]

Examples of usage:
[Example 1]
[Example 2]
```

### 4. Testing the Public Micro-Agent

Before submitting:
- Test the agent with various prompts.
- Verify trigger words activate the agent correctly.
- Ensure instructions are clear and comprehensive.
- Check for potential conflicts with existing agents.

### 5. Submission Process

Submit a pull request with:
- The new micro-agent file.
- Updated documentation if needed.
- Description of the agent's purpose and capabilities.

### Example Public Micro-Agent Implementation

Here's a template for a new micro-agent:

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

Remember that micro-agents are a powerful way to extend OpenHands' capabilities in specific domains. Well-designed
agents can significantly improve the system's ability to handle specialized tasks.
