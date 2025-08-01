# Enhanced Timeout Handling Implementation

This document summarizes the comprehensive timeout handling improvements implemented to address GitHub issues #8706, #8960, #9149, #9736, and #9978.

## Overview

The enhanced timeout system provides:
- **Context-aware timeouts**: Different timeout values for different operation types
- **Progressive timeouts**: Increasing timeout values for retry attempts
- **Adaptive timeouts**: Timeout values that adjust based on operation complexity
- **Better error messages**: Informative timeout messages with recovery suggestions
- **Configurable timeouts**: Easy configuration for different use cases

## Key Components

### 1. Timeout Configuration (`openhands/core/config/timeout_config.py`)
- **TimeoutType enum**: Categorizes operations (command, runtime, LLM, file, browser, async)
- **TimeoutConfig class**: Manages timeout values, strategies, and limits
- **TimeoutContext class**: Provides context-aware timeout handling with recovery suggestions

### 2. Timeout Manager (`openhands/utils/timeout_manager.py`)
- **TimeoutManager class**: Central timeout management with operation tracking
- **Context managers**: Async and sync timeout operation contexts
- **Complexity estimation**: Automatic timeout adjustment based on operation characteristics
- **Active operation monitoring**: Track and monitor running operations

### 3. Configuration Utility (`openhands/utils/timeout_configurator.py`)
- **Command-line tool**: Easy timeout configuration management
- **Preset configurations**: Pre-defined timeout settings for different use cases
- **Configuration persistence**: Save/load timeout settings from JSON files

### 4. Enhanced Integration
- **Runtime integration**: Automatic timeout type detection for actions
- **Event system**: Enhanced timeout metadata in events
- **Bash session**: Context-aware timeout suggestions and recovery options
- **Async utilities**: Improved timeout error handling

## Timeout Types and Default Values

| Type | Default | Max | Description |
|------|---------|-----|-------------|
| `COMMAND_DEFAULT` | 120s | 1800s | Regular bash commands |
| `COMMAND_LONG_RUNNING` | 600s | 3600s | Build, compilation, installation |
| `COMMAND_INTERACTIVE` | 30s | 300s | Interactive commands (editors) |
| `COMMAND_NETWORK` | 180s | 600s | Network operations (git, curl) |
| `RUNTIME_INIT` | 300s | 900s | Runtime initialization |
| `LLM_REQUEST` | 120s | 600s | LLM API requests |
| `FILE_READ` | 30s | 300s | File reading operations |
| `BROWSER_NAVIGATION` | 60s | 300s | Page navigation |

## Features

### 1. Automatic Timeout Type Detection
Commands are automatically categorized:
```bash
git clone https://repo.git  # -> COMMAND_NETWORK (180s)
make -j4                    # -> COMMAND_LONG_RUNNING (600s)
vim file.txt               # -> COMMAND_INTERACTIVE (30s)
ls -la                     # -> COMMAND_DEFAULT (120s)
```

### 2. Progressive Timeouts
Retry attempts get longer timeouts:
- Attempt 1: Base timeout (120s)
- Attempt 2: 1.5x base (180s)
- Attempt 3: 2x base (240s)
- Attempt 4: 3x base (360s)

### 3. Adaptive Timeouts
Timeouts adjust based on complexity:
- Large files: Higher timeout multiplier
- Network operations: 1.5x multiplier
- CPU-intensive: 2x multiplier
- I/O-intensive: 1.5x multiplier

### 4. Enhanced Error Messages
Timeout errors include:
- Operation details and elapsed time
- Attempt number for retries
- Context-specific recovery suggestions
- Command-specific troubleshooting tips

Example:
```
Operation 'git clone https://github.com/large-repo.git' timed out after 180.0 seconds (attempt 1)

Suggestions:
• Git operations may be slow due to repository size or network
• Try using --depth=1 for shallow clones
• Check network connectivity and repository accessibility

Recovery Options:
• Send empty command '' to wait for more output
• Send 'C-c' to interrupt the current process
• Use a longer timeout for future similar commands
```

## Configuration Options

### Command Line Tool
```bash
# Show current configuration
python -m openhands.utils.timeout_configurator show

# Set specific timeout
python -m openhands.utils.timeout_configurator set command_default 180

# Apply preset
python -m openhands.utils.timeout_configurator preset development

# Show available presets
python -m openhands.utils.timeout_configurator recommendations
```

### Available Presets
- **Development**: Shorter timeouts for faster feedback (60s default)
- **Production**: Longer, stable timeouts (180s default)
- **CI/CD**: Build-focused timeouts (1800s long-running)
- **Research**: Very long timeouts for complex operations (3600s long-running)

### Programmatic Configuration
```python
from openhands.core.config.timeout_config import TimeoutConfig, TimeoutType
from openhands.utils.timeout_manager import TimeoutManager

config = TimeoutConfig()
config.default_timeouts[TimeoutType.COMMAND_DEFAULT] = 180.0
manager = TimeoutManager(config)

async with manager.async_timeout_operation(
    TimeoutType.COMMAND_NETWORK,
    "git_operation",
    attempt=2,
    complexity_factor=1.5
) as context:
    await git_operation()
```

## Integration Points

### 1. Sandbox Configuration
```python
# Enhanced timeout configuration in sandbox config
class SandboxConfig(BaseModel):
    timeout_config: TimeoutConfig = Field(default_factory=TimeoutConfig)
```

### 2. Runtime Integration
```python
# Automatic timeout type detection and application
async def _handle_action(self, event: Action) -> None:
    if event.timeout is None:
        timeout_type = self._get_timeout_type_for_action(event)
        timeout_value = self.timeout_manager.timeout_config.get_timeout(
            timeout_type,
            attempt=getattr(event, 'timeout_attempt', 1),
            complexity_factor=getattr(event, 'timeout_complexity_factor', 1.0)
        )
        event.set_enhanced_timeout(timeout_value, timeout_type.value, ...)
```

### 3. Event System Enhancement
```python
# Enhanced timeout metadata in events
event.timeout_type                    # The timeout type used
event.timeout_attempt                 # The attempt number
event.timeout_complexity_factor       # The complexity factor applied
```

### 4. Bash Session Improvements
```python
# Context-aware timeout suggestions
def _get_timeout_suggestions(self, command: str, timeout_type: str) -> str:
    # Returns command-specific recovery suggestions
```

## Testing

Comprehensive test suite in `tests/unit/test_enhanced_timeout.py`:
- Timeout configuration functionality
- Progressive and adaptive timeout calculation
- Timeout context management
- Runtime integration
- Timeout suggestion generation

## Backward Compatibility

The enhanced timeout system is fully backward compatible:
- Existing `set_hard_timeout()` calls continue to work
- Default timeout behavior is preserved
- New features are opt-in through configuration

## Performance Impact

Minimal performance overhead:
- Timeout type detection: O(1) string matching
- Configuration lookup: O(1) dictionary access
- Context management: Lightweight object creation
- Operation tracking: Optional feature

## Files Modified

### New Files
- `openhands/core/config/timeout_config.py` - Core timeout configuration
- `openhands/utils/timeout_manager.py` - Timeout management system
- `openhands/utils/timeout_configurator.py` - Configuration utility
- `tests/unit/test_enhanced_timeout.py` - Comprehensive test suite
- `docs/timeout_handling.md` - User documentation

### Modified Files
- `openhands/core/config/sandbox_config.py` - Added timeout config integration
- `openhands/events/event.py` - Enhanced timeout metadata support
- `openhands/runtime/base.py` - Automatic timeout type detection
- `openhands/runtime/utils/bash.py` - Context-aware timeout suggestions
- `openhands/utils/async_utils.py` - Enhanced timeout error handling

## Benefits

1. **Reduced timeout-related failures**: Context-appropriate timeout values
2. **Better user experience**: Informative error messages with recovery suggestions
3. **Improved reliability**: Progressive timeouts for retry scenarios
4. **Easy configuration**: Command-line tools and presets for different use cases
5. **Better debugging**: Operation tracking and monitoring capabilities
6. **Adaptive behavior**: Automatic timeout adjustment based on operation complexity

## Future Enhancements

Potential future improvements:
1. **Machine learning-based timeout prediction**: Learn optimal timeouts from usage patterns
2. **Dynamic timeout adjustment**: Real-time timeout adjustment based on system load
3. **Timeout analytics**: Collect and analyze timeout patterns for optimization
4. **Integration with monitoring systems**: Export timeout metrics for observability
5. **User-specific timeout profiles**: Per-user timeout preferences and learning

## Migration Guide

For users wanting to adopt the new timeout system:

1. **Review current timeout issues**: Identify operations that frequently timeout
2. **Choose appropriate preset**: Select development, production, CI/CD, or research preset
3. **Apply configuration**: Use the configurator tool to apply settings
4. **Monitor and adjust**: Use operation tracking to fine-tune timeout values
5. **Leverage new features**: Use progressive timeouts for retry logic

The enhanced timeout system provides a solid foundation for reliable, user-friendly timeout handling in OpenHands while maintaining full backward compatibility with existing code.
