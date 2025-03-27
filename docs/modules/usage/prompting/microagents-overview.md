# Microagents Overview

Microagents are specialized prompts that enhance OpenHands with domain-specific knowledge, repository-specific context
and task-specific workflows. They help by providing expert guidance, automating common tasks, and ensuring
consistent practices across projects.

## Microagent Categories

Currently OpenHands supports two categories of microagents:

- [Repository-specific Microagents](./microagents-repo): Repository-specific context and guidelines for OpenHands.
- [Public Microagents](./microagents-public): General guidelines triggered by keywords for all OpenHands users.

A microagent is classified as repository-specific or public depending on its location:

- Repository-specific microagents are located in a repository's `.openhands/microagents/` directory
- Public microagents are located in the official OpenHands repository inside the `/microagents` folder

When OpenHands works with a repository, it:

1. Loads repository-specific instructions from `.openhands/microagents/` if present in the repository.
2. Loads public knowledge microagents triggered by keywords in conversations
3. Loads public task microagents when explicitly requested by the user

See current [Public Microagents](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/) at the official repository.

## Microagent Format

All microagents use markdown files with YAML frontmatter that have special instructions to help OpenHands accomplish
tasks:

```
---
name: <Name of the microagent>
type: <MicroAgent type>
version: <MicroAgent version>
agent: <The agent type (Typically CodeActAgent)>
triggers:
- <Optional keywords triggering the microagent. If triggers are removed, it will always be included>
---

<Markdown with any special guidelines, instructions, and prompts that OpenHands should follow.
Check out the specific documentation for each microagent on best practices for more information.>
```
