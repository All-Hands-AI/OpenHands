# Keyword-Triggered Microagents

## Purpose

Keyword-triggered microagents provide OpenHands with specific instructions that are activated when certain keywords
appear in the prompt. This is useful for tailoring behavior based on particular tools, languages, or frameworks.

## Usage

These microagents are only loaded when a prompt includes one of the trigger words.

## Frontmatter Syntax

Frontmatter is required for keyword-triggered microagents. It must be placed at the top of the file,
above the guidelines.

Enclose the frontmatter in triple dashes (---) and include the following fields:

| Field      | Description                                      | Required | Default          |
|------------|--------------------------------------------------|----------|------------------|
| `triggers` | A list of keywords that activate the microagent. | Yes      | None             |
| `agent`    | The agent this microagent applies to.            | No       | 'CodeActAgent'   |


## Example

Keyword-triggered microagent file example located at `.openhands/microagents/yummy.md`:
```
---
triggers:
- yummyhappy
- happyyummy
---

The user has said the magic word. Respond with "That was delicious!"
```

[See examples of microagents triggered by keywords in the official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents)
