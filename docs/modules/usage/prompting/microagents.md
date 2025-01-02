# Micro-Agents

OpenHands uses specialized micro-agents to handle specific tasks and contexts efficiently. These micro-agents are small, focused components that provide specialized behavior and knowledge for particular scenarios.

## Overview

Micro-agents are defined in markdown files under the `openhands/agenthub/codeact_agent/micro/` directory. Each micro-agent is configured with:

- A unique name
- The agent type (typically CodeActAgent)
- Trigger keywords that activate the agent
- Specific instructions and capabilities

## Available Micro-Agents

### GitHub Agent
**File**: `github.md`
**Triggers**: `github`, `git`

The GitHub agent specializes in GitHub API interactions and repository management. It:
- Has access to a `GITHUB_TOKEN` for API authentication
- Follows strict guidelines for repository interactions
- Handles branch management and pull requests
- Uses the GitHub API instead of web browser interactions

Key features:
- Branch protection (prevents direct pushes to main/master)
- Automated PR creation
- Git configuration management
- API-first approach for GitHub operations

### NPM Agent
**File**: `npm.md`
**Triggers**: `npm`

Specializes in handling npm package management with specific focus on:
- Non-interactive shell operations
- Automated confirmation handling using Unix 'yes' command
- Package installation automation

### Custom Micro-Agents

You can create your own micro-agents by adding new markdown files to the micro-agents directory. Each file should follow this structure:

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

## Best Practices

When working with micro-agents:

1. **Use Appropriate Triggers**: Ensure your commands include the relevant trigger words to activate the correct micro-agent
2. **Follow Agent Guidelines**: Each agent has specific instructions and limitations - respect these for optimal results
3. **API-First Approach**: When available, use API endpoints rather than web interfaces
4. **Automation Friendly**: Design commands that work well in non-interactive environments

## Integration

Micro-agents are automatically integrated into OpenHands' workflow. They:
- Monitor incoming commands for their trigger words
- Activate when relevant triggers are detected
- Apply their specialized knowledge and capabilities
- Follow their specific guidelines and restrictions

## Example Usage

```bash
# GitHub agent example
git checkout -b feature-branch
git commit -m "Add new feature"
git push origin feature-branch

# NPM agent example
yes | npm install package-name
```

For more information about specific agents, refer to their individual documentation files in the micro-agents directory.

## Contributing a Micro-Agent

To contribute a new micro-agent to OpenHands, follow these guidelines:

### 1. Planning Your Micro-Agent

Before creating a micro-agent, consider:
- What specific problem or use case will it address?
- What unique capabilities or knowledge should it have?
- What trigger words make sense for activating it?
- What constraints or guidelines should it follow?

### 2. File Structure

Create a new markdown file in `openhands/agenthub/codeact_agent/micro/` with a descriptive name (e.g., `docker.md` for a Docker-focused agent).

### 3. Required Components

Your micro-agent file must include:

1. **Front Matter**: YAML metadata at the start of the file:
```markdown
---
name: your_agent_name
agent: CodeActAgent
triggers:
- trigger_word1
- trigger_word2
---
```

2. **Instructions**: Clear, specific guidelines for the agent's behavior:
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

### 4. Best Practices for Micro-Agent Development

1. **Clear Scope**: Keep the agent focused on a specific domain or task
2. **Explicit Instructions**: Provide clear, unambiguous guidelines
3. **Useful Examples**: Include practical examples of common use cases
4. **Safety First**: Include necessary warnings and constraints
5. **Integration Awareness**: Consider how the agent interacts with other components

### 5. Testing Your Micro-Agent

Before submitting:
1. Test the agent with various prompts
2. Verify trigger words activate the agent correctly
3. Ensure instructions are clear and comprehensive
4. Check for potential conflicts with existing agents

### 6. Example Implementation

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

### 7. Submission Process

1. Create your micro-agent file in the correct directory
2. Test thoroughly
3. Submit a pull request with:
   - The new micro-agent file
   - Updated documentation if needed
   - Description of the agent's purpose and capabilities

Remember that micro-agents are a powerful way to extend OpenHands' capabilities in specific domains. Well-designed agents can significantly improve the system's ability to handle specialized tasks.
