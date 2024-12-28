# OpenHands MicroAgents

This directory contains MicroAgents that extend OpenHands' capabilities with specialized knowledge and workflow templates.

## Directory Structure

```
microagents/
├── official/           # Official OpenHands microagents
│   ├── knowledge/     # Knowledge-based agents
│   │   ├── repo/     # Repository-triggered agents
│   │   └── keyword/  # Keyword-triggered agents
│   └── templates/    # Template-based agents
│       └── workflows/
└── community/         # Community-contributed agents
    ├── knowledge/
    └── templates/
```

## Types of MicroAgents

### 1. Knowledge-based Agents

These agents provide specialized knowledge and can be triggered in two ways:

#### Repository-based Triggers
Activated based on repository name patterns:
```yaml
trigger_type: repository
trigger_pattern: "org/repo-*"
priority: 100  # Higher number = higher priority
```

#### Keyword-based Triggers
Activated by specific keywords in user input:
```yaml
trigger_type: keyword
triggers:
  - keyword1
  - keyword2
```

### 2. Template-based Agents

These require user selection and input:
```yaml
template_type: workflow
template: |
  Template text with ${VARIABLES}
inputs:
  - name: VARIABLE_NAME
    type: string
    required: true
```

## Contributing

### Adding a New Agent

1. Choose the appropriate directory:
   - `official/` for core OpenHands team
   - `community/` for community contributions

2. Select the agent type:
   - Knowledge-based: `knowledge/repo/` or `knowledge/keyword/`
   - Template-based: `templates/workflows/`

3. Create a YAML file with the required fields:
   ```yaml
   name: agent_name
   version: 1.0.0
   author: username
   agent: CodeActAgent
   category: development|testing|deployment|etc
   ...
   ```

4. Add comprehensive documentation:
   - Clear description
   - Detailed capabilities
   - Usage examples
   - Requirements

5. Submit a pull request:
   - Follow the standard PR template
   - Include test cases
   - Update relevant documentation

### Best Practices

1. **Naming**:
   - Use descriptive, lowercase names
   - Include the technology/domain in the name

2. **Documentation**:
   - Clear purpose and use cases
   - Complete examples
   - List all requirements

3. **Testing**:
   - Test all trigger conditions
   - Validate templates
   - Check for conflicts

4. **Maintenance**:
   - Keep agents up to date
   - Monitor for issues
   - Respond to feedback

## License

All microagents are subject to the same license as OpenHands. See the root LICENSE file for details.