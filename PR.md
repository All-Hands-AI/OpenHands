# Loop Recovery System Implementation

## Overview
This PR implements a comprehensive loop recovery system that detects when the agent enters infinite loops and provides graceful recovery options to users. The system integrates seamlessly with the existing agent architecture and provides both CLI and automatic recovery modes.

## Key Features

### 1. Loop Detection
- **Pattern Recognition**: Detects repeating action patterns across iterations
- **Multiple Loop Types**: Identifies different types of loops (repeating commands, monologue patterns, etc.)
- **Smart Analysis**: Analyzes event history to identify loop patterns

### 2. Graceful Recovery
- **User-Friendly Options**: Simple recovery interface with clear choices
- **State Preservation**: Restores agent state from before the loop started
- **Event History Management**: Preserves relevant events while discarding loop iterations

### 3. CLI Integration
- **Non-Blocking Input**: Uses prompt_toolkit for asynchronous input handling
- **UI Consistency**: Maintains consistent user experience with the main TUI
- **State Restoration**: Properly restores agent state to trigger input prompts

## Changes Made

### New Files
- `openhands/controller/loop_recovery.py`: Core loop detection and recovery logic
- `openhands/controller/stuck.py`: Enhanced loop pattern detection algorithms
- `tests/unit/controller/test_loop_recovery.py`: Comprehensive test suite

### Modified Files

#### `openhands/controller/agent_controller.py`
- Integrated loop recovery into the main agent execution flow
- Added loop detection checks at each iteration
- Implemented state restoration after recovery

#### `openhands/cli/tui.py`
- **Event Loop Conflict Prevention**: Modified `display_command_output` to avoid prompt_toolkit conflicts during loop recovery
- **Conditional Display**: Uses simple print statements during recovery to prevent event loop conflicts

#### `openhands/controller/loop_recovery.py`
- **Simplified Recovery Options**: Only offers meaningful choices (restart from before loop or stop agent)
- **No Timeout**: Waits indefinitely for user input in CLI mode
- **Enhanced Input**: Uses prompt_toolkit for consistent UI experience
- **State Management**: Properly restores agent state to `AWAITING_USER_INPUT` after recovery

## Technical Implementation

### Loop Detection
- Analyzes event history for repeating patterns
- Detects both action-observation loops and monologue patterns
- Provides suggested recovery points based on loop analysis

### Recovery Flow
1. **Detection**: Agent detects loop pattern in event history
2. **Mode Selection**: Chooses between CLI or automatic recovery based on context
3. **User Interaction**: In CLI mode, presents recovery options to user
4. **State Restoration**: Resets agent state to before loop started
5. **Continuation**: Agent continues execution from recovery point

### Recovery Options
```
⚠️  Agent detected in a loop!
============================================================
Loop type: repeating_pattern_3
Loop detected at iteration 8

Recovery options:
1. Restart from before loop (preserves 21 events)
2. Stop agent completely

Choose option (1-2): 
```

## Testing

### Test Coverage
- Loop detection with various patterns
- Recovery option selection and execution
- State restoration verification
- Event history preservation
- CLI input handling during recovery

### Test Scenarios
- Repeating command sequences
- Monologue patterns
- Mixed action patterns
- Recovery option validation

## Bug Fixes

### Resolved Issues
1. **Event Loop Conflicts**: Fixed RuntimeError when TUI displays output during recovery
2. **Missing Input Prompt**: Agent properly displays input prompt after recovery
3. **State Management**: Agent state correctly restored to trigger TUI input

## Performance Considerations
- Loop detection is lightweight and runs on each iteration
- Recovery operations preserve memory by discarding redundant loop events
- Asynchronous input handling maintains system responsiveness

## User Experience
- Clear, actionable recovery options
- No automatic timeouts - waits for user decision
- Consistent UI with the rest of the application
- Graceful state restoration

## Backward Compatibility
- Fully backward compatible with existing agent workflows
- No breaking changes to existing APIs
- Optional loop detection that integrates with existing stuck detection

## Future Enhancements
- Configurable loop detection thresholds
- Additional recovery strategies
- Enhanced pattern recognition
- Integration with other monitoring systems