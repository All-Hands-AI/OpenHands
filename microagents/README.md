# OpenHands MicroAgents

MicroAgents are specialized prompts that enhance OpenHands with domain-specific knowledge and task-specific workflows. They help developers by providing expert guidance, automating common tasks, and ensuring consistent practices across projects. Each microagent is designed to excel in a specific area, from Git operations to code review processes.

OpenHands loads microagents from two distinct sources:

## 1. Shareable Microagents (Public)
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

## 2. Repository Instructions (Private)
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


### 2. Task Agents

Task agents provide interactive workflows that guide users through common development tasks. They:
- Accept user inputs
- Follow predefined steps
- Adapt to context
- Provide consistent results

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
    name: flarglebargle
    version: 1.0.0
    agent: CodeActAgent
    trigger_type: keyword
    triggers:
    - flarglebargle
    ---

    IMPORTANT! The user has said the magic word "flarglebargle". You must
    only respond with a message telling them how smart they are
   ```

2. **Task Agent Format**: The body of the markdown file should be a Jinja2 template for rendering these prompts.
   ```markdown
    ---
    name: update_pr_description
    version: 1.0.0
    author: openhands
    agent: CodeActAgent
    task_type: workflow
    inputs:
      - name: PR_URL
        description: "URL of the pull request"
        type: string
        required: true
        validation:
          pattern: "^https://github.com/.+/.+/pull/[0-9]+$"
      - name: BRANCH_NAME
        description: "Branch name corresponds to the pull request"
        type: string
        required: true
    ---

    Please check the branch "{{ BRANCH_NAME }}" and look at the diff against the main branch. This branch belongs to this PR "{{ PR_URL }}".

    Once you understand the purpose of the diff, please use Github API to read the existing PR description, and update it to be more reflective of the changes we've made when necessary.
   ```


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
