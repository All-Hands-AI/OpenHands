# Add timeout indicator in CLI when language model times out

## Problem

Currently, when the language model times out during CLI usage, users see a generic error message without clear indication that the issue is specifically a timeout. This makes it difficult for users to understand what went wrong and how to resolve it.

## Current Behavior

1. LLM timeout errors (`litellm.Timeout`) are caught in the agent controller
2. They are treated as generic errors with no specific `RuntimeStatus`
3. The CLI displays them via `ErrorObservation` and `display_error()` function
4. Users see a generic error message without timeout-specific guidance

## Proposed Solution

### Backend Changes

1. **Add new RuntimeStatus**: Add `ERROR_LLM_TIMEOUT` to `openhands/runtime/runtime_status.py`
2. **Update exception handling**: Modify `_react_to_exception` in `openhands/controller/agent_controller.py` to specifically handle `Timeout` exceptions
3. **Set appropriate status**: When a timeout occurs, set the runtime status to `ERROR_LLM_TIMEOUT`

### CLI Changes

1. **Detect timeout errors**: Modify `display_error()` in `openhands/cli/tui.py` to detect timeout-related error messages
2. **Display timeout indicator**: Show a clear "Language model timed out" message
3. **Provide helpful guidance**: Include link to timeout configuration documentation at https://docs.all-hands.dev

## Implementation Strategy

### Step 1: Add RuntimeStatus
```python
# In openhands/runtime/runtime_status.py
ERROR_LLM_TIMEOUT = 'STATUS$ERROR_LLM_TIMEOUT'
```

### Step 2: Update Exception Handling
```python
# In openhands/controller/agent_controller.py, in _react_to_exception method
elif isinstance(e, Timeout):
    runtime_status = RuntimeStatus.ERROR_LLM_TIMEOUT
    self.state.last_error = runtime_status.value
```

### Step 3: Update CLI Display
```python
# In openhands/cli/tui.py, modify display_error function
def display_error(error: str) -> None:
    error = error.strip()

    if error:
        # Check if this is a timeout error
        if 'ERROR_LLM_TIMEOUT' in error or 'timeout' in error.lower():
            title = 'Language Model Timed Out'
            timeout_message = (
                f"{error}\n\n"
                "The language model request timed out. You can:\n"
                "• Increase the timeout with --llm-timeout <seconds>\n"
                "• Check your network connection\n"
                "• Try again with a shorter prompt\n\n"
                "For more configuration options, see:\n"
                "https://docs.all-hands.dev/modules/usage/configuration-options"
            )
            display_text = timeout_message
        else:
            title = 'Error'
            display_text = error

        container = Frame(
            TextArea(
                text=display_text,
                read_only=True,
                style='ansired',
                wrap_lines=True,
            ),
            title=title,
            style='ansired',
        )
        print_formatted_text('')
        print_container(container)
```

## Benefits

1. **Clear user feedback**: Users immediately understand the issue is a timeout
2. **Actionable guidance**: Provides specific steps to resolve the issue
3. **Documentation link**: Directs users to comprehensive configuration options
4. **Consistent with GUI**: Aligns CLI behavior with web interface timeout handling

## Testing

- [ ] Test with actual LLM timeout scenarios
- [ ] Verify timeout indicator displays correctly
- [ ] Ensure documentation link is accessible
- [ ] Test with different timeout values via `--llm-timeout`

## Related

- PR #9683: Add CLI argument for LLM timeout configuration
- Documentation: https://docs.all-hands.dev/modules/usage/configuration-options
