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
