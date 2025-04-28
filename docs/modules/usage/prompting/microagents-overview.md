# Microagents Overview

Microagents are specialized prompts that enhance OpenHands with domain-specific knowledge.
They provide expert guidance, automate common tasks, and ensure consistent practices across projects.

## Microagent Types

Currently OpenHands supports the following types of microagents:

- [General Repository Microagents](./microagents-repo): General guidelines for OpenHands about the repository.
- [Keyword-Triggered Microagents](./microagents-keyword): Guidelines activated by specific keywords in prompts.

To customize OpenHands' behavior, create a .openhands/microagents/ directory in the root of your repository and
add `<microagent_name>.md` files inside.

:::note
Loaded microagents take up space in the context window.
These microagents, alongside user messages, inform OpenHands about the task and the environment.
:::

Example repository structure:

```
some-repository/
└── .openhands/
    └── microagents/
        └── repo.md            # General repository guidelines
        └── trigger_this.md    # Microagent triggered by specific keywords
        └── trigger_that.md    # Microagent triggered by specific keywords
```

## Microagents Frontmatter Requirements

Each microagent file may include frontmatter that provides additional information. In some cases, this frontmatter
is required:

| Microagent Type                  | Frontmatter Requirement                               |
|----------------------------------|-------------------------------------------------------|
| `General Repository Microagents` | Required only if more than one of this type exists.   |
| `Keyword-Triggered Microagents`  | Required.                                             |
