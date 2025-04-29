# General Repository Microagents

## Purpose

General guidelines for OpenHands to work more effectively with the repository.

## Microagent File

Create a general repository microagent (example: `.openhands/microagents/repo.md`) to include
project-specific instructions, team practices, coding standards, and architectural guidelines that are relevant for
**all** prompts in that repository.

## Frontmatter Syntax

The frontmatter for this type of microagent is optional, unless you plan to include more than one general
repository microagent.

Frontmatter should be enclosed in triple dashes (---) and may include the following fields:

| Field     | Description                             | Required                                                           | Default        |
|-----------|-----------------------------------------|--------------------------------------------------------------------|----------------|
| `name`    | A unique identifier for the microagent  | Required only if using more than one general repository microagent | 'default'      |
| `agent`   | The agent this microagent applies to    | No                                                                 | 'CodeActAgent' |

## Example

```
---
name: repo
---

This project is a TODO application that allows users to track TODO items.

To set it up, you can run `npm run build`.
Always make sure the tests are passing before committing changes. You can run the tests by running `npm run test`.
```

[See more examples of general repository microagents here.](https://github.com/All-Hands-AI/OpenHands/tree/main/.openhands/microagents)
