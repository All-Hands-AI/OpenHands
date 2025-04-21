# Keyword-Triggered Microagents

You may want to create microagents for a repository (example: `.openhands/microagents/trigger-keyword.md`) that only 
activate when specific keywords are present in a prompt. To do this, you must add frontmatter to the top of the 
microagent file, in addition to the guidelines. The frontmatter format is as follows:

Enclosed by triple dashes (`---`). The required fields are:

| Field      | Description                                     |
| ---------- |-------------------------------------------------|
| `name`     | A unique identifier for the microagent          |
| `triggers` | A list of keywords that activate the microagent |

Example of a microagent triggerd by keywords:
```
---
name: magic_word
triggers:
- yummyhappy
- happyyummy
---

The user has said the magic word. Respond with "That was delicious!"
```

Keyword-triggered microagents:
- Monitor incoming commands for their trigger words.
- Activate when relevant triggers are detected.
- Apply their specialized knowledge and capabilities.
- Follow their specific guidelines and restrictions.

[See examples of microagents triggered by keywords in the official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge)