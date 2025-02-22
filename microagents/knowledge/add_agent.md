# Add Microagent Helper

This agent helps create new microagents in the `.openhands/microagents` directory by providing guidance and templates.

## Triggers
The agent activates when the conversation includes:
- "new agent"
- "new microagent"
- "create agent"
- "create an agent"
- "create microagent"
- "create a microagent"
- "add agent"
- "add an agent"
- "add microagent"
- "add a microagent"
- "microagent template"

## What are Microagents?

Microagents are specialized prompts that provide context and capabilities for specific domains or tasks. They are activated by trigger words in the conversation and help the AI assistant understand:
- What capabilities are available
- How to use specific APIs or tools
- What limitations exist
- How to handle common scenarios

For detailed information, see:
- [Microagents Overview](https://docs.all-hands.dev/modules/usage/prompting/microagents-overview)
- [Example GitHub Microagent](https://github.com/All-Hands-AI/OpenHands/blob/main/microagents/knowledge/github.md)

## Template Structure

A microagent markdown file should include:

```markdown
# Agent Name

Brief description of what this agent does.

## Triggers
List of words/phrases that activate this agent:
- "trigger word 1"
- "trigger word 2"

## Capabilities
What the agent can do, including:
- Available APIs
- Environment variables
- Tools or commands

## Usage Examples
```code
Example code or usage
```

## Important Notes
- Limitations
- Security considerations
- Best practices

## Error Handling
Common errors and how to handle them
```

## Creating a New Agent

To create a new microagent:
1. Create a markdown file in `.openhands/microagents/`
2. Name it appropriately (e.g., `github.md`, `google_workspace.md`)
3. Include all required sections
4. Ensure trigger words are specific and relevant
5. Document any credentials or environment variables
6. Provide clear usage examples

## Best Practices

- Keep trigger words specific to avoid false activations
- Document all credentials and access tokens
- Include error handling guidance
- Provide working code examples
- Reference external documentation when available
- Consider security implications
- Keep the prompt focused and concise

## Example Implementation

Here's a minimal example:

```markdown
# Example Agent

Handles interaction with ExampleService API.

## Triggers
- "example service"
- "example api"

## Capabilities
Access to ExampleService API:
- API_KEY: ${EXAMPLE_API_KEY}
- Base URL: https://api.example.com

## Usage Examples
```python
import requests
response = requests.get(
    "https://api.example.com/data",
    headers={"Authorization": "Bearer ${EXAMPLE_API_KEY}"}
)
```

## Important Notes
- Rate limited to 100 requests/minute
- Requires valid API key

## Error Handling
- 401: Check API key
- 429: Rate limit exceeded
```
