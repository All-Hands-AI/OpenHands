# Agent Mode Toggle

The Agent Mode Toggle feature allows you to switch between two different agent modes:

1. **Execute Mode** (default): Full capabilities with the CodeActAgent, which can modify code and execute commands
2. **Read-only Mode**: Restricted capabilities with the ReadOnlyAgent, which can only explore and analyze code

## Why Use Different Modes?

- **Safety**: Ensure no changes are made during the exploration phase
- **Clarity**: Clear indication of the agent's current capabilities
- **Control**: Decide when to transition from planning to execution
- **Workflow**: Support a natural workflow of exploration → planning → implementation

## How to Use

1. **Toggle Switch**: Click the toggle switch in the agent control bar to switch between modes
   - Blue toggle: Execute Mode (default)
   - Amber toggle: Read-only Mode

2. **Mode Indicators**:
   - The current mode is displayed in the agent status bar
   - System messages indicate when the mode changes

## Available Tools in Each Mode

### Execute Mode (CodeActAgent)

All tools are available, including:
- File editing (`str_replace_editor`)
- Command execution (`execute_bash`)
- Python code execution (`execute_ipython_cell`)
- Web browsing (`browser`, `web_read`)
- Thinking and finishing (`think`, `finish`)

### Read-only Mode (ReadOnlyAgent)

Only non-destructive tools are available:
- File viewing (`view`)
- File searching (`grep`, `glob`)
- Web reading (`web_read`)
- Thinking and finishing (`think`, `finish`)

## Best Practices

1. **Start in Read-only Mode** for new codebases to safely explore without making changes
2. **Switch to Execute Mode** when you're ready to implement changes
3. **Return to Read-only Mode** when you want to explore different parts of the codebase

## Technical Details

The agent mode toggle uses OpenHands' agent delegation mechanism:
- When toggling to Read-only Mode, the system delegates to a ReadOnlyAgent
- When toggling back to Execute Mode, the delegation ends and returns to the CodeActAgent
- Context is preserved between mode switches