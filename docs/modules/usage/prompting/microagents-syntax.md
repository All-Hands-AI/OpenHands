# Microagents Syntax

Microagents are defined using markdown files with YAML frontmatter that specify their behavior, triggers, and capabilities.

Find below a comprehensive description of the frontmatter syntax and other details about how to use each type of microagent available at OpenHands.

## Frontmatter Schema

Every microagent requires a YAML frontmatter section at the beginning of the file, enclosed by triple dashes (`---`). The fields are:

| Field      | Description                                        | Required                 | Used By          |
| ---------- | -------------------------------------------------- | ------------------------ | ---------------- |
| `name`     | Unique identifier for the microagent               | Yes                      | All types        |
| `type`     | Type of microagent: `repo`, `knowledge`, or `task` | Yes                      | All types        |
| `version`  | Version number (Semantic versioning recommended)   | Yes                      | All types        |
| `agent`    | The agent type (typically `CodeActAgent`)          | Yes                      | All types        |
| `author`   | Creator of the microagent                          | No                       | All types        |
| `triggers` | List of keywords that activate the microagent      | Yes for knowledge agents | Knowledge agents |
| `inputs`   | Defines required user inputs for task execution    | Yes for task agents      | Task agents      |

## Core Fields

### `agent`

**Purpose**: Specifies which agent implementation processes the microagent (typically `CodeActAgent`).

- Defines a single agent responsible for processing the microagent
- Must be available in the OpenHands system (see the [agent hub](https://github.com/All-Hands-AI/OpenHands/tree/main/openhands/agenthub))
- If the specified agent is not active, the microagent will not be used

### `triggers`

**Purpose**: Defines keywords that activate the `knowledge` microagent.

**Example**:

```yaml
triggers:
  - kubernetes
  - k8s
  - docker
  - security
  - containers cluster
```

**Key points**:

- Can include both single words and multi-word phrases
- Case-insensitive matching is typically used
- More specific triggers (like "docker compose") prevent false activations
- Multiple triggers increase the chance of activation in relevant contexts
- Unique triggers like "flarglebargle" can be used for testing or special functionality
- Triggers should be carefully chosen to avoid unwanted activations or conflicts with other microagents
- Common terms used in many conversations may cause the microagent to be activated too frequently

When using multiple triggers, the microagent will be activated if any of the trigger words or phrases appear in the
conversation.

### `inputs`

**Purpose**: Defines parameters required from the user when a `task` microagent is activated.

**Schema**:

```yaml
inputs:
  - name: INPUT_NAME # Used with {{ INPUT_NAME }}
    description: 'Description of what this input is for'
    required: true # Optional, defaults to true
```

**Key points**:

- The `name` and `description` properties are required for each input
- The `required` property is optional and defaults to `true`
- Input values are referenced in the microagent body using double curly braces (e.g., `{{ INPUT_NAME }}`)
- All inputs defined will be collected from the user before the task microagent executes

**Variable Usage**: Reference input values using double curly braces `{{ INPUT_NAME }}`.

## Example Formats

### Repository Microagent

Repository microagents provide context and guidelines for a specific repository.

- Located at: `.openhands/microagents/repo.md`
- Automatically loaded when working with the repository
- Only one per repository

The `Repository` microagent is loaded specifically from `.openhands/microagents/repo.md` and serves as the main
repository-specific instruction file. This single file is automatically loaded whenever OpenHands works with that repository
without requiring any keyword matching or explicit call from the user.

[See the example in the official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/blob/main/.openhands/microagents/repo.md?plain=1)

### Knowledge Microagent

Provides specialized domain expertise triggered by keywords.

You can find several real examples of `Knowledge` microagents in the [offical OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge)

### Task Microagent

When explicitly asked by the user, will guide through interactive workflows with specific inputs.

You can find several real examples of `Tasks` microagents in the [offical OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/tasks)

## Markdown Content Best Practices

After the frontmatter, compose the microagent body using Markdown syntax. Examples of elements you can include are:

- Clear, concise instructions outlining the microagent's purpose and responsibilities
- Specific guidelines and constraints the microagent should adhere to
- Relevant code snippets and practical examples to illustrate key points
- Step-by-step procedures for task agents, guiding users through workflows

**Design Tips**:

- Keep microagents focused with a clear purpose
- Provide specific guidelines rather than general advice
- Use distinctive triggers for knowledge agents
- Keep content concise to minimize context window usage
- Break large microagents into smaller, focused ones

Aim for clarity, brevity, and practicality in your writing. Use formatting like bullet points, code blocks, and emphasis to enhance readability and comprehension.

Remember that balancing microagents details with user input space is important for maintaining effective interactions.
