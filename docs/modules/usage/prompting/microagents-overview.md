# Microagents Overview

Microagents are specialized prompts that enhance OpenHands with domain-specific knowledge. 
They provide expert guidance, automate common tasks, and ensure consistent practices across projects.

## Microagent Types

Currently OpenHands supports the following types of microagents:

- [General Repository Microagents](./microagents-repo): General guidelines for OpenHands about the repository.
- [Keyword-Triggered Microagents](./microagents-keyword): Guidelines activated by specific keywords in prompts.

Each repository can customize OpenHands' behavior by creating a `.openhands/microagents/` directory in the 
repository's root and placing `<microagent_name>.md` files in this directory.

:::note
Keep in mind that loaded microagents take up space in the context window. 
The microagents alongside the user messages inform OpenHands about the task and the environment.
:::

Example of how a repository's microagents might look like:

```
some-repository/
└── .openhands/
    └── microagents/
        └── repo.md            # General repository guidelines
        └── trigger_this.md    # Microagent triggered by specific keywords
        └── trigger_that.md    # Microagent triggered by specific keywords
```
