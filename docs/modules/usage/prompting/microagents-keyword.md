# Keyword-Triggered Microagents

## Purpose

Keyword-triggered microagents provide OpenHands with specific instructions that are activated when certain keywords
appear in the prompt. This is useful for tailoring behavior based on particular tools, languages, or frameworks.

## Microagent File

Create a keyword-triggered microagent (example: `.openhands/microagents/trigger-keyword.md`) to include instructions
that activate only for prompts with specific keywords.

## Frontmatter Syntax

Frontmatter is required for keyword-triggered microagents. It must be placed at the top of the file,
above the guidelines.

Enclose the frontmatter in triple dashes (---) and include the following fields:

| Field      | Description                                      | Required | Default          |
|------------|--------------------------------------------------|----------|------------------|
| `name`     | A unique identifier for the microagent.          | Yes      | 'default'        |
| `type`     | Type of microagent. Must be set to `knowledge`.  | Yes      | 'repo'           |
| `triggers` | A list of keywords that activate the microagent. | Yes      | None             |
| `agent`    | The agent this microagent applies to.            | No       | 'CodeActAgent'   |


## Example

```
---
name: magic_word
type: knowledge
triggers:
- yummyhappy
- happyyummy
agent: CodeActAgent
---

The user has said the magic word. Respond with "That was delicious!"
```

Keyword-triggered microagents:
- Monitor incoming prompts for specified trigger words.
- Activate when relevant triggers are detected.
- Apply their specialized knowledge and capabilities.
- Follow defined guidelines and restrictions.

[See examples of microagents triggered by keywords in the official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents)
