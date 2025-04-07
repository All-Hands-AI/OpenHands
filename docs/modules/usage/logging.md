# Logging in OpenHands

OpenHands provides a robust and configurable logging system that helps developers track application behavior, debug issues, and monitor LLM interactions. This guide covers the key aspects of OpenHands' logging functionality.

## Environment Variables

OpenHands' logging behavior can be customized through several environment variables:

### Core Logging Controls

- `LOG_LEVEL`: Sets the logging level (default: 'INFO')
  - Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - Can also be enabled by setting `DEBUG=true`

- `LOG_TO_FILE`: Enables file-based logging (default: false)
  - When enabled, logs are written to `logs/openhands_YYYY-MM-DD.log`
  - Automatically enabled when in DEBUG mode

### JSON Logging

- `LOG_JSON`: Enables structured JSON logging (default: false)
  - When enabled, logs are output in JSON format for better machine readability
  - Useful for log aggregation and analysis systems

- `LOG_JSON_LEVEL_KEY`: Customizes the key name for log levels in JSON output (default: 'level')
  - Example: `{"timestamp": "2025-04-07 10:00:00", "level": "INFO", "message": "..."}`

### Debug Options

- `DEBUG`: Enables debug mode (default: false)
  - Sets LOG_LEVEL to DEBUG
  - Enables stack traces for errors
  - Automatically enables file logging

- `DEBUG_LLM`: Enables detailed LLM interaction logging (default: false)
  - **WARNING**: May expose sensitive information like API keys
  - Requires explicit confirmation when enabled
  - Should never be enabled in production

- `DEBUG_RUNTIME`: Enables runtime environment debugging (default: false)
  - Streams Docker container logs
  - Useful for debugging sandbox environments

### Event Logging

- `LOG_ALL_EVENTS`: Enables verbose event logging (default: false)
  - Logs all events with additional context
  - Useful for debugging agent behavior

## Log File Structure

When file logging is enabled (`LOG_TO_FILE=true`), logs are organized as follows:

```
logs/
├── openhands_YYYY-MM-DD.log    # Main application log
└── llm/                        # LLM interaction logs
    └── [session]/              # Session-specific logs
        ├── prompt_001.log      # LLM prompts
        └── response_001.log    # LLM responses
```

- Session directories are named:
  - In debug mode: `YY-MM-DD_HH-MM`
  - Otherwise: `default`

## Security Features

### SensitiveDataFilter

OpenHands includes a sophisticated filter to prevent sensitive data from appearing in logs:

1. **Environment Variables**
   - Automatically masks values from environment variables containing:
     - SECRET
     - _KEY
     - _CODE
     - _TOKEN

2. **Known Sensitive Patterns**
   - Masks common sensitive values like:
     - API keys
     - Access tokens
     - Authentication credentials
     - AWS credentials
     - GitHub tokens

Example:
```python
# Original log message
"API key: sk-1234567890, GitHub token: ghp_abcdef"

# Filtered log message
"API key: ******, GitHub token: ******"
```

## Best Practices

1. **Production Settings**
   - Keep `DEBUG` and `DEBUG_LLM` disabled
   - Consider enabling `LOG_JSON` for structured logging
   - Use appropriate `LOG_LEVEL` (INFO or WARNING recommended)

2. **Development Settings**
   - Enable `DEBUG` for detailed logging
   - Use `LOG_TO_FILE` to persist logs
   - Enable `LOG_ALL_EVENTS` when debugging agent behavior

3. **Security Considerations**
   - Never enable `DEBUG_LLM` in production
   - Regularly review logs for accidentally exposed sensitive data
   - Use `SensitiveDataFilter` for custom logging implementations

