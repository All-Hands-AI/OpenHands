# General Microagents

## Purpose

General guidelines for OpenHands to work more effectively with the repository.

## Usage

These microagents are always loaded as part of the context.

## Frontmatter Syntax

The frontmatter for this type of microagent is optional.

Frontmatter should be enclosed in triple dashes (---) and may include the following fields:

| Field     | Description                             | Required | Default        |
|-----------|-----------------------------------------|----------|----------------|
| `agent`   | The agent this microagent applies to    | No       | 'CodeActAgent' |

## Example

General microagent file example located at `.openhands/microagents/repo.md`:
```
This project is a TODO application that allows users to track TODO items.

To set it up, you can run `npm run build`.
Always make sure the tests are passing before committing changes. You can run the tests by running `npm run test`.
```

[See more examples of general microagents here.](https://github.com/All-Hands-AI/OpenHands/tree/main/.openhands/microagents)
