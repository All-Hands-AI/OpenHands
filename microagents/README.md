# OpenHands MicroAgents

OpenHands loads microagents from two distinct sources:

## 1. Repository Instructions (Private)
Each repository can have its own instructions in `.openhands/microagents/repo.md`. These instructions are:
- Private to that repository
- Automatically loaded when working with that repository
- Perfect for repository-specific guidelines and team practices

Example repository structure:
```
your-repository/
└── .openhands/
    └── microagents/
        └── repo.md    # Repository-specific instructions
```

## 2. Shareable Microagents (Public)
This directory (`OpenHands/microagents/`) contains shareable microagents that are:
- Available to all OpenHands users
- Maintained in the OpenHands repository
- Perfect for reusable knowledge and common workflows

Directory structure:
```
OpenHands/microagents/
├── knowledge/     # Keyword-triggered expertise
│   ├── git.yaml      # Git operations
│   ├── testing.yaml  # Testing practices
│   └── docker.yaml   # Docker guidelines
└── tasks/        # Interactive workflows
    ├── pr_review.yaml   # PR review process
    ├── bug_fix.yaml     # Bug fixing workflow
    └── feature.yaml     # Feature implementation
```

## Loading Order

When OpenHands works with a repository, it:
1. Loads repository-specific instructions from `.openhands/microagents/repo.md` if present
2. Loads relevant knowledge agents based on keywords in conversations
3. Makes task agents available for user selection

## Types of MicroAgents

### 1. Knowledge Agents

Knowledge agents provide specialized expertise that's triggered by keywords in conversations. They help with:
- Language best practices
- Framework guidelines
- Common patterns
- Tool usage

Example `knowledge/testing.yaml`:
```yaml
name: testing_guidelines
version: 1.0.0
author: openhands
agent: CodeActAgent
trigger_type: keyword
triggers: 
  - test
  - testing
  - jest
file_patterns:  # Optional: only trigger for specific files
  - "*.test.ts"
  - "*.spec.ts"
description: "Testing best practices"
knowledge: |
  # Testing Guidelines
  
  ## Key Principles
  1. Use Jest for unit tests
  2. Follow AAA pattern...
```

### 2. Task Agents

Task agents provide interactive workflows that guide users through common development tasks. They:
- Accept user inputs
- Follow predefined steps
- Adapt to context
- Provide consistent results

Example `tasks/pr_review.yaml`:
```yaml
name: pr_review
version: 1.0.0
author: openhands
agent: CodeActAgent
task_type: workflow
description: "PR review workflow"
prompt: |
  I'll help you review PR ${PR_URL} with these steps:
  1. Code Quality...
  ${FOCUS_AREAS}
inputs:
  - name: PR_URL
    description: "URL of the pull request"
    type: string
    required: true
    validation:
      pattern: "^https://github.com/.+/.+/pull/[0-9]+$"
```

## Contributing

### When to Contribute

1. **Knowledge Agents** - When you have:
   - Language/framework best practices
   - Tool usage patterns
   - Common problem solutions
   - General development guidelines

2. **Task Agents** - When you have:
   - Repeatable workflows
   - Multi-step processes
   - Common development tasks
   - Standard procedures

### Best Practices

1. **For Knowledge Agents**:
   - Choose distinctive triggers
   - Focus on one area of expertise
   - Include practical examples
   - Use file patterns when relevant
   - Keep knowledge general and reusable

2. **For Task Agents**:
   - Break workflows into clear steps
   - Validate user inputs
   - Provide helpful defaults
   - Include usage examples
   - Make steps adaptable

### Format Guidelines

All microagents use markdown files with YAML frontmatter:

1. **Knowledge Agent Format**:
   ```markdown
   ---
   name: unique_name         # Lowercase, descriptive
   version: 1.0.0           # Semantic versioning
   author: your_name        # Your GitHub username
   agent: CodeActAgent      # Agent type
   trigger_type: keyword
   triggers:                # List of trigger words
     - trigger1
     - trigger2
   file_patterns:           # Optional file patterns
     - "*.ts"
     - "*.js"
   ---

   # Title

   ## Overview
   Clear description of the agent's purpose...

   ## Guidelines
   - Guideline 1
   - Guideline 2

   ## Examples
   ```bash
   example command
   ```
   ```

2. **Task Agent Format**:
   ```markdown
   ---
   name: unique_name
   version: 1.0.0
   author: your_name
   agent: CodeActAgent
   task_type: workflow
   inputs:
     - name: INPUT_NAME
       description: "..."
       type: string|number|boolean
       required: true|false
   ---

   # Task Title

   I'll help you with ${INPUT_NAME}...

   ## Steps
   1. First step...
   2. Second step...

   ## Example Usage
   ```yaml
   inputs:
     INPUT_NAME: "example value"
   ```
   ```

### Testing Your Agent

Before submitting:
1. Test all trigger words (for knowledge agents)
2. Try all input combinations (for task agents)
3. Verify markdown formatting
4. Check for clear, helpful output

### Submission Process

1. Create your agent file in the appropriate directory:
   - `knowledge/` for expertise
   - `tasks/` for workflows
2. Test thoroughly
3. Submit a pull request with:
   - Clear description of the agent's purpose
   - Example usage
   - Test cases

## License

All microagents are subject to the same license as OpenHands. See the root LICENSE file for details.