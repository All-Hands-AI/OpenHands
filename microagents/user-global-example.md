---
name: user-global-example
type: knowledge
triggers:
  - user global microagent
  - global microagent example
  - custom microagent
---

# User Global Microagent Example

This is an example of a user global microagent that you can place in your `~/.openhands/microagents/` directory. This file itself should NOT be placed there - it's just a reference example.

## How to Create Your Own User Global Microagents

1. Create the directory if it doesn't exist:
   ```bash
   mkdir -p ~/.openhands/microagents
   ```

2. Create a markdown file with YAML frontmatter:
   ```markdown
   ---
   name: my-python-style
   type: knowledge
   triggers:
     - python style
     - my python style
     - python formatting
   ---

   # My Python Style Guide

   Here are my personal Python style preferences:

   - Use 4 spaces for indentation
   - Maximum line length of 88 characters (Black default)
   - Use double quotes for strings
   - etc.
   ```

3. Save the file in `~/.openhands/microagents/` with a `.md` extension, for example: `~/.openhands/microagents/my-python-style.md`

4. OpenHands will automatically load this microagent when it starts, and it will be available across all repositories you work with.

## Creating Global Repository Microagents

You can also create global repository microagents that apply to all repositories:

```markdown
---
name: global-guidelines
type: repo
---

# My Global Repository Guidelines

These are guidelines I want to follow for all my repositories:

- Always write tests for new features
- Keep functions small and focused
- Document public APIs
- Follow semantic versioning for releases
- Use descriptive commit messages
```

Save this as `~/.openhands/microagents/global-guidelines.md` and it will be loaded for all repositories.

## Microagent Frontmatter Fields

- `name`: (required) The name of the microagent
- `type`: (required) Either `knowledge` or `repo`
- `triggers`: (required for knowledge microagents) List of keywords that trigger the microagent
- `version`: (optional) Version of the microagent, defaults to "1.0.0"
- `agent`: (optional) The agent that should use this microagent, defaults to "CodeActAgent"

## Loading Order

Remember that microagents are loaded in this order:
1. Global microagents from the OpenHands package
2. User global microagents from `~/.openhands/microagents/`
3. Repository-specific microagents from `.openhands/microagents/` in the repository

This means your user global microagents can override the behavior of bundled microagents, and repository-specific microagents can override both.
