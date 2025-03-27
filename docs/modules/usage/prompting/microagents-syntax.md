# Microagents Syntax

Microagents are defined using markdown files with YAML frontmatter that specify their behavior, triggers, and capabilities.

Below you find a comprehensive description of the frontmatter syntax and other details about how to use each type of microagent available at OpenHands.

## Frontmatter Schema

Every microagent requires a YAML frontmatter section at the beginning of the file, enclosed by triple dashes (`---`). The following table describes all possible frontmatter fields:

| Field      | Description                                        | Required                 | Used By          |
| ---------- | -------------------------------------------------- | ------------------------ | ---------------- |
| `name`     | Unique identifier for the microagent               | Yes                      | All types        |
| `type`     | Type of microagent: `repo`, `knowledge`, or `task` | Yes                      | All types        |
| `version`  | Version number (Semantic versioning recommended)   | Yes                      | All types        |
| `agent`    | The agent type (typically `CodeActAgent`)          | Yes                      | All types        |
| `author`   | Creator of the microagent                          | No                       | All types        |
| `triggers` | List of keywords that activate the microagent      | Yes for knowledge agents | Knowledge agents |
| `inputs`   | Defines required user inputs for task execution    | Yes for task agents      | Task agents      |

### Understanding the `agent` field

The `agent` field specifies which agent implementation should process the microagent. Currently, most microagents use `CodeActAgent` as the designated agent type. Key points about the `agent` field:

- It defines a single agent responsible for processing the microagent
- Multiple agents cannot be specified in a single microagent
- The specified agent must be available in the OpenHands system
- If a microagent is triggered but the specified agent is not the active agent, the microagent will not be used
- Each microagent is tightly coupled to its designated agent implementation

This field ensures that microagents are processed by the appropriate agent implementation that understands how to interpret and execute the microagent's instructions.

### Understanding the `triggers` field (for knowledge Microagents)

The `triggers` field is used exclusively in `Knowledge` microagents to define keywords that will activate the microagent when detected in a conversation. Examples of triggers from existing OpenHands microagents:

```yaml
# Simple single-word triggers (kubernetes.md)
triggers:
- kubernetes
- k8s
- kube

# Multi-word and concept-based triggers (security.md)
triggers:
  - security
  - vulnerability
  - authentication
  - authorization
  - permissions

# Specialized unique triggers (flarglebargle.md)
triggers:
- flarglebargle
```

Important characteristics of the `triggers` field:

- Can include both single words and multi-word phrases
- Case-insensitive matching is typically used
- More specific triggers (like "docker compose") prevent false activations
- Multiple triggers increase the chance of activation in relevant contexts
- Unique triggers like "flarglebargle" can be used for testing or special functionality
- Triggers should be carefully chosen to avoid unwanted activations or conflicts with other microagents
- Common terms used in many conversations may cause the microagent to be activated too frequently

When using multiple triggers, the microagent will be activated if any of the trigger words or phrases appear in the conversation.

### The `inputs` field Schema (for Task Microagents)

For `Task` microagents, the `inputs` field should follow this schema:

```yaml
inputs:
  - name: INPUT_NAME # Name of the input variable (used with {{ INPUT_NAME }})
    description: 'Description of what this input is for'
    type: string # Data type (string, number, boolean) - Optional, defaults to string
    required: true # Whether the input is required - Optional, defaults to true
    validation: # Optional validation rules
      pattern: '^regex$' # Regex pattern for validation
```

Important characteristics of the `inputs` field:

- The `name` and `description` properties are required for each input
- The `type` property is optional and defaults to `string`
- The `required` property is optional and defaults to `true`
- The `validation` object with a `pattern` field is optional but recommended for inputs that need validation
- Input values are referenced in the microagent body using double curly braces (e.g., `{{ INPUT_NAME }}`)
- All inputs defined will be collected from the user before the task microagent executes
- The OpenHands system will validate inputs based on the defined schema before passing them to the microagent

Example of a `Task` microagent with required and optional inputs:

```yaml
inputs:
  - name: PR_URL
    description: 'URL of the pull request'
    type: string
    required: true
    validation:
      pattern: '^https://github.com/.+/.+/pull/[0-9]+$'
  - name: BRANCH_NAME
    description: 'Branch name corresponds to the pull request'
    type: string
    required: true
  - name: REVIEWER
    description: 'GitHub username of the reviewer to assign'
    type: string
    required: false
```

The validation uses standard regex patterns to ensure inputs match expected formats. This is particularly helpful for ensuring URLs, file paths, and other structured inputs are properly formatted before execution.

## Common Microagent Formats

### Repository Microagent Example

Repository microagents provide repository-specific context and guidelines. There can only be one primary `repo.md` file in a repository's `.openhands/microagents/` directory.

The `Repository` microagent is loaded specifically from `.openhands/microagents/repo.md` and serves as the main repository-specific instruction file. This single file is automatically loaded whenever OpenHands works with that repository without requiring any keyword matching or explicit call from the user.

You can find a real example in the [official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/blob/main/.openhands/microagents/repo.md?plain=1):

### Knowledge Microagent Example

Knowledge microagents provide specialized domain expertise triggered by keywords.

You can find several real examples in the [official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/knowledge):

### Task Microagent Example

Task microagents guide users through interactive workflows with specific inputs.

You can find several real examples in the [official OpenHands repository](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents/tasks):

## Variable Interpolation

In task microagents, use double curly braces `{{ }}` to reference input variables. For example, `{{ PR_URL }}` will be replaced with the actual PR URL provided by the user.

## Markdown Content

After the frontmatter, you should include detailed markdown content with:

1. **Clear instructions**: What the microagent should do
2. **Guidelines**: Specific rules or constraints to follow
3. **Examples**: Practical examples demonstrating proper usage
4. **Code snippets**: When relevant for demonstrating concepts
5. **Step-by-step procedures**: For task agents, provide clear steps

### Best Practices

1. **Keep it focused**: Each microagent should have a clear purpose and scope
2. **Be specific**: Provide detailed guidelines rather than general advice
3. **Include examples**: Real-world examples help illustrate proper usage
4. **Use code blocks**: Format code examples with appropriate syntax highlighting
5. **Document edge cases**: Include handling of common exceptions or special cases
6. **Define clear triggers**: For knowledge agents, choose distinctive keywords
7. **Validate inputs**: For task agents, include proper validation rules
8. **Version appropriately**: Update the version number when making changes

### Context Window Considerations

Microagents occupy space in the LLM's context window. To optimize performance:

1. Keep instructions concise and focused
2. Remove unnecessary examples or verbose explanations
3. Prioritize the most important information
4. Consider breaking very large microagents into smaller, more focused ones
5. For repository agents, focus on unique aspects rather than generic guidelines

Remember that balancing microagents details with user input space is important for maintaining effective interactions.
