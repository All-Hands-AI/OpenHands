# Ctrl+C Handling Improvements

## Summary

Simplified the overly complex Ctrl+C handling implementation in the OpenHands CLI to make it more reliable and easier to understand.

## Problems Addressed

1. **Second Ctrl+C not registering properly** - The original implementation had complex queue-based communication that could miss signals
2. **Overly complex multiprocessing** - Many methods were unnecessarily wrapped in separate processes
3. **No reset of Ctrl+C count** - The count wasn't reset when starting new message processing
4. **Unnecessary queue communication** - Status and settings methods didn't need separate processes

## Solution

### 1. Simplified Signal Handler (`simple_signal_handler.py`)

- **Direct signal handling** in the main process instead of complex queue communication
- **Simple Ctrl+C counting** with immediate force kill on second press within 3 seconds
- **Clear process management** with direct process termination
- **Reset functionality** to clear count when starting new operations

Key features:
- First Ctrl+C: Graceful termination (SIGTERM)
- Second Ctrl+C (within 3 seconds): Force kill (SIGKILL)
- Automatic count reset after 3 seconds
- Manual count reset via `reset_count()`

### 2. Simplified Process Runner (`simple_process_runner.py`)

- **Minimal multiprocessing** - Only the `process_message` method runs in a subprocess
- **Direct method calls** for status, settings, and other operations
- **Simple API** with clear process lifecycle management
- **No queue communication** for methods that don't need it

Key features:
- `process_message()`: Runs in subprocess for isolation
- `get_status()`, `get_settings()`, etc.: Run directly in main process
- `cleanup()`: Simple process termination
- `current_process` property for signal handler integration

### 3. Updated Main CLI (`agent_chat.py`)

- **Simplified imports** using the new signal handler and process runner
- **Reset Ctrl+C count** when starting new message processing
- **Direct method calls** for commands that don't need process isolation
- **Cleaner error handling** and resource cleanup

## Files Modified

### New Files
- `openhands_cli/simple_signal_handler.py` - Simplified signal handling
- `openhands_cli/simple_process_runner.py` - Minimal process wrapper

### Modified Files
- `openhands_cli/agent_chat.py` - Updated to use simplified components
- `openhands_cli/simple_main.py` - Updated imports

### Test Files
- `test_basic_signal.py` - Basic signal handler test
- `manual_test_ctrl_c.py` - Manual Ctrl+C testing

## Key Improvements

1. **Reliability**: Direct signal handling eliminates race conditions
2. **Simplicity**: Removed complex queue-based communication
3. **Performance**: Most operations run directly in main process
4. **Maintainability**: Clear, simple code that's easy to understand
5. **User Experience**: Consistent Ctrl+C behavior with immediate force kill option

## Testing

The implementation includes test scripts to verify:
- Basic signal handler functionality
- Ctrl+C counting and reset behavior
- Process termination (graceful and force)
- Integration with the CLI

## Usage

The simplified implementation maintains the same external API:
- First Ctrl+C: Attempts graceful pause/termination
- Second Ctrl+C (within 3 seconds): Force kills the process immediately
- Count resets automatically or when starting new operations

## Migration

The changes are backward compatible with the existing CLI interface. The complex `ProcessSignalHandler` and `ProcessBasedConversationRunner` classes are replaced with simpler equivalents that provide the same functionality with better reliability.