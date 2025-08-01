# Enhanced Timeout Handling in OpenHands

OpenHands now features a comprehensive timeout handling system that provides better control, context-aware timeouts, and improved error recovery for various operations.

## Overview

The enhanced timeout system addresses common timeout-related issues by providing:

- **Context-aware timeouts**: Different timeout values for different types of operations
- **Progressive timeouts**: Increasing timeout values for retry attempts
- **Adaptive timeouts**: Timeout values that adjust based on operation complexity
- **Better error messages**: Informative timeout messages with recovery suggestions
- **Configurable timeouts**: Easy configuration of timeout values for different scenarios

## Timeout Types

The system categorizes operations into different timeout types:

### Command Execution Timeouts
- `COMMAND_DEFAULT`: Regular bash commands (default: 120s)
- `COMMAND_LONG_RUNNING`: Build, compilation, installation commands (default: 600s)
- `COMMAND_INTERACTIVE`: Interactive commands like editors (default: 30s)
- `COMMAND_NETWORK`: Network operations like git, curl, wget (default: 180s)

### Runtime Operation Timeouts
- `RUNTIME_INIT`: Runtime initialization (default: 300s)
- `RUNTIME_SHUTDOWN`: Runtime shutdown (default: 60s)
- `RUNTIME_HEALTH_CHECK`: Health check operations (default: 30s)

### LLM Operation Timeouts
- `LLM_REQUEST`: LLM API requests (default: 120s)
- `LLM_STREAMING`: Streaming LLM responses (default: 300s)

### File Operation Timeouts
- `FILE_READ`: File reading operations (default: 30s)
- `FILE_WRITE`: File writing operations (default: 60s)
- `FILE_LARGE_OPERATION`: Large file operations (default: 300s)

### Browser Operation Timeouts
- `BROWSER_NAVIGATION`: Page navigation (default: 60s)
- `BROWSER_INTERACTION`: Element interactions (default: 30s)
- `BROWSER_WAIT`: Waiting for elements (default: 10s)

### General Async Timeouts
- `ASYNC_GENERAL`: General async operations (default: 15s)
- `ASYNC_BACKGROUND`: Background tasks (default: 300s)

## Features

### 1. Automatic Timeout Type Detection

The system automatically detects the appropriate timeout type based on the command or operation:

```python
# Network commands get network timeout
git clone https://github.com/example/repo.git  # -> COMMAND_NETWORK (180s)

# Build commands get long-running timeout
make -j4  # -> COMMAND_LONG_RUNNING (600s)

# Interactive commands get interactive timeout
vim file.txt  # -> COMMAND_INTERACTIVE (30s)

# Regular commands get default timeout
ls -la  # -> COMMAND_DEFAULT (120s)
```

### 2. Progressive Timeouts

For retry attempts, timeouts increase progressively:

- Attempt 1: Base timeout (e.g., 120s)
- Attempt 2: 1.5x base timeout (e.g., 180s)
- Attempt 3: 2x base timeout (e.g., 240s)
- Attempt 4: 3x base timeout (e.g., 360s)

### 3. Adaptive Timeouts

Timeouts adjust based on operation complexity:

```python
# Large file operations get longer timeouts
complexity_factor = estimate_complexity_factor(
    data_size=50*1024*1024,  # 50MB file
    network_involved=True,
    io_intensive=True
)
# Results in timeout = base_timeout * complexity_factor
```

### 4. Enhanced Error Messages

When timeouts occur, you get detailed error messages with recovery suggestions:

```
Operation 'git clone https://github.com/large-repo.git' timed out after 180.0 seconds (attempt 1) (timeout was 180.0s)

Suggestions:
• Git operations may be slow due to repository size or network
• Try using --depth=1 for shallow clones
• Check network connectivity and repository accessibility

Timeout Recovery Options:
• Send empty command '' to wait for more output
• Send 'C-c' to interrupt the current process
• Use a longer timeout for future similar commands
```

## Configuration

### Using the Configuration File

Create or modify `~/.openhands/timeout_config.json`:

```json
{
  "default_timeouts": {
    "command_default": 120.0,
    "command_long_running": 600.0,
    "command_network": 180.0
  },
  "enable_progressive_timeout": true,
  "enable_adaptive_timeout": true,
  "no_change_timeout": 30.0,
  "warning_threshold_ratio": 0.8
}
```

### Using the Command Line Tool

```bash
# Show current configuration
python -m openhands.utils.timeout_configurator show

# Set a specific timeout
python -m openhands.utils.timeout_configurator set command_default 180

# Apply a preset configuration
python -m openhands.utils.timeout_configurator preset development

# Show available presets
python -m openhands.utils.timeout_configurator recommendations

# Reset to defaults
python -m openhands.utils.timeout_configurator reset
```

### Available Presets

#### Development
Optimized for development work with shorter timeouts:
- `command_default`: 60s
- `command_long_running`: 300s
- `no_change_timeout`: 20s

#### Production
Optimized for production with longer, more stable timeouts:
- `command_default`: 180s
- `command_long_running`: 900s
- `no_change_timeout`: 60s

#### CI/CD
Optimized for CI/CD pipelines with build-focused timeouts:
- `command_default`: 120s
- `command_long_running`: 1800s
- `no_change_timeout`: 45s

#### Research
Optimized for research work with very long timeouts:
- `command_default`: 300s
- `command_long_running`: 3600s
- `no_change_timeout`: 120s

### Programmatic Configuration

```python
from openhands.core.config.timeout_config import TimeoutConfig, TimeoutType
from openhands.utils.timeout_manager import TimeoutManager

# Create custom timeout configuration
config = TimeoutConfig()
config.default_timeouts[TimeoutType.COMMAND_DEFAULT] = 180.0
config.enable_progressive_timeout = True

# Use with timeout manager
manager = TimeoutManager(config)

# Use timeout context
async with manager.async_timeout_operation(
    TimeoutType.COMMAND_NETWORK,
    "git_clone_operation",
    attempt=2,
    complexity_factor=1.5
) as context:
    # Your operation here
    await some_network_operation()
```

## Integration with Existing Code

### Runtime Integration

The enhanced timeout system is automatically integrated with the runtime:

```python
# Actions automatically get appropriate timeouts
action = CmdRunAction(command="npm install")
# Automatically gets COMMAND_LONG_RUNNING timeout (600s)

# You can also set custom timeouts
action.set_enhanced_timeout(
    timeout_value=900.0,
    timeout_type=TimeoutType.COMMAND_LONG_RUNNING.value,
    attempt=1,
    complexity_factor=2.0
)
```

### Event System Integration

Events support enhanced timeout metadata:

```python
event.timeout_type  # The timeout type used
event.timeout_attempt  # The attempt number
event.timeout_complexity_factor  # The complexity factor applied
```

## Monitoring and Debugging

### Active Operations Tracking

Monitor currently active operations:

```python
from openhands.utils.timeout_manager import get_timeout_manager

manager = get_timeout_manager()
active_ops = manager.get_active_operations()

for op_id, info in active_ops.items():
    print(f"Operation: {info['operation_name']}")
    print(f"Type: {info['timeout_type']}")
    print(f"Elapsed: {info['elapsed_time']:.1f}s")
    print(f"Remaining: {info['remaining_time']:.1f}s")
    print(f"Progress: {info['progress_ratio']:.1%}")
```

### Timeout Warnings

The system can show warnings when operations are taking longer than expected:

```
Operation 'large_build_process' has been running for 480.0s (timeout in 120.0s). Type: command_long_running
```

## Best Practices

### 1. Choose Appropriate Timeout Types

- Use `COMMAND_NETWORK` for operations that involve network I/O
- Use `COMMAND_LONG_RUNNING` for builds, installations, and compilations
- Use `COMMAND_INTERACTIVE` for operations that may require user input

### 2. Set Realistic Complexity Factors

```python
# For large file operations
complexity_factor = manager.estimate_complexity_factor(
    "file_processing",
    data_size=file_size,
    io_intensive=True
)

# For network operations
complexity_factor = manager.estimate_complexity_factor(
    "network_request",
    network_involved=True,
    data_size=expected_response_size
)
```

### 3. Handle Timeout Errors Gracefully

```python
try:
    result = await manager.wait_with_timeout(
        some_operation(),
        TimeoutType.COMMAND_DEFAULT,
        "my_operation"
    )
except asyncio.TimeoutError as e:
    logger.error(f"Operation timed out: {e}")
    # Implement retry logic or fallback
```

### 4. Use Progressive Timeouts for Retries

```python
for attempt in range(1, 4):
    try:
        async with manager.async_timeout_operation(
            TimeoutType.COMMAND_NETWORK,
            "network_operation",
            attempt=attempt
        ):
            result = await network_operation()
            break
    except asyncio.TimeoutError:
        if attempt == 3:
            raise
        logger.warning(f"Attempt {attempt} timed out, retrying...")
```

## Troubleshooting

### Common Issues

1. **Operations timing out too quickly**
   - Check if the correct timeout type is being used
   - Consider increasing the default timeout for that type
   - Use adaptive timeouts with appropriate complexity factors

2. **Operations taking too long**
   - Enable timeout warnings to get early notifications
   - Check if operations are stuck waiting for input
   - Consider breaking large operations into smaller parts

3. **Inconsistent timeout behavior**
   - Ensure progressive timeouts are enabled for retries
   - Check that complexity factors are being calculated correctly
   - Verify timeout configuration is loaded properly

### Debugging Commands

```bash
# Check current timeout configuration
python -m openhands.utils.timeout_configurator show

# Test timeout detection for specific commands
python -c "
from openhands.events.action.commands import CmdRunAction
from openhands.runtime.base import Runtime
action = CmdRunAction(command='your_command_here')
# Test timeout type detection
"
```

## Migration from Old Timeout System

The enhanced timeout system is backward compatible. Existing code will continue to work, but you can gradually migrate to use the new features:

### Before
```python
action.set_hard_timeout(300, blocking=True)
```

### After
```python
action.set_enhanced_timeout(
    timeout_value=300,
    timeout_type=TimeoutType.COMMAND_LONG_RUNNING.value,
    attempt=1,
    complexity_factor=1.0,
    blocking=True
)
```

## Contributing

To add support for new timeout types or improve timeout detection:

1. Add new timeout types to `TimeoutType` enum in `timeout_config.py`
2. Update default and maximum timeout values in `TimeoutConfig`
3. Enhance `_get_timeout_type_for_action()` in `runtime/base.py`
4. Add appropriate timeout suggestions in `bash.py`
5. Update tests and documentation

## Related Issues

This enhanced timeout system addresses the following GitHub issues:
- #8706: Timeout handling improvements
- #8960: Better timeout error messages
- #9149: Context-aware timeout configuration
- #9736: Progressive timeout for retries
- #9978: Adaptive timeout based on operation complexity