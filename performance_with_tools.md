# Performance Testing with Tool Calls

## Overview

This document describes the enhanced performance testing architecture that includes tool calls to better simulate real-world OpenHands usage patterns. Instead of simple prompt-response testing, we now test the complete tool interaction workflow.

## Why Tool Call Testing Matters

- **Real-world simulation**: OpenHands frequently uses tools (bash, file editing, etc.)
- **Latency impact**: Tool calls add multiple round-trips and processing overhead
- **Performance bottlenecks**: Tool parsing and execution can reveal different performance characteristics
- **Complete workflow**: Tests the full LLM → Tool → LLM → Summary cycle

## Test Architecture

### 3-Step Tool Call Workflow

Each performance test now follows this standardized 3-step process:

#### Step 1: Initial Tool Request
- **Prompt**: "What is the product of 45 and 126? Use the math tool to calculate this."
- **Tool Definition**: Provide a `math` tool that can compute products
- **Expected**: LLM should respond with a tool call to `math(a=45, b=126)`
- **Measure**: Time to generate tool call response

#### Step 2: Tool Execution & Response
- **Action**: Execute the math tool function (45 × 126 = 5670)
- **Response**: Send tool result back to LLM as a tool message
- **Expected**: LLM acknowledges the result
- **Measure**: Time to process tool result

#### Step 3: Summary Request
- **Prompt**: "Please summarize what just happened in our conversation."
- **Expected**: LLM provides a summary of the math calculation
- **Measure**: Time to generate summary response

### Message History Tracking

All messages and responses are preserved in a `messages` array:

```python
messages = [
    {"role": "user", "content": "What is the product of 45 and 126? Use the math tool."},
    {"role": "assistant", "content": "", "tool_calls": [...]},  # Step 1 response
    {"role": "tool", "tool_call_id": "...", "content": "5670"},  # Step 2 tool result
    {"role": "assistant", "content": "The product is 5670."},  # Step 2 response
    {"role": "user", "content": "Please summarize what just happened."},
    {"role": "assistant", "content": "I calculated 45 × 126 = 5670..."}  # Step 3 response
]
```

## Tool Definition

The `math` tool is defined consistently across all tests:

```python
MATH_TOOL = {
    "type": "function",
    "function": {
        "name": "math",
        "description": "Perform mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The mathematical operation to perform",
                    "enum": ["add", "subtract", "multiply", "divide"]
                },
                "a": {
                    "type": "number",
                    "description": "First number"
                },
                "b": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["operation", "a", "b"]
        }
    }
}
```

## Performance Metrics

Each test measures:

- **Step 1 Duration**: Time to generate initial tool call
- **Step 2 Duration**: Time to process tool result
- **Step 3 Duration**: Time to generate summary
- **Total Duration**: End-to-end workflow time
- **Tool Call Accuracy**: Whether LLM correctly used the tool
- **Response Quality**: Whether all steps completed successfully

## Security Considerations

### Environment Variables

All tests now use secure environment variable-based authentication:

- **LiteLLM Tests**: Use `LITELLM_PROXY_API_KEY` and `LITELLM_BASE_URL`
- **Native API Tests**: Use `GEMINI_API_KEY` (for direct Google API calls)
- **OpenHands Tests**: Use `LITELLM_PROXY_API_KEY` and `LITELLM_BASE_URL` (routed through LiteLLM)

### Credential Handling

- ✅ **Secure**: Read credentials from environment variables only
- ✅ **No Hardcoding**: No API keys in source code or documentation
- ✅ **Error Handling**: Graceful failure when credentials are missing
- ✅ **Logging**: No credential values in logs or output

```python
# Secure credential handling example
api_key = os.getenv('LITELLM_PROXY_API_KEY')
base_url = os.getenv('LITELLM_BASE_URL')

if not api_key:
    print('❌ LITELLM_PROXY_API_KEY environment variable not set')
    return

# Never log or print the actual key values
print(f'✅ Using base URL: {base_url}')  # OK to log URL
print('✅ API key configured')  # OK to confirm presence
```

## Implementation Files

### Core Utility
- `test_utils.py`: Shared tool call testing utilities

### Test Files
- `test_thinking_budget.py`: Primary thinking/reasoning with tool calls
- `test_litellm_comprehensive.py`: LiteLLM performance with tool calls
- `test_native_gemini.py`: Native API baseline with tool calls
- `test_openhands_gemini_fix.py`: OpenHands fix verification with tool calls
- `run_performance_tests.py`: Orchestrator for all tool-based tests

## Expected Results

Tool call testing typically shows:

- **Higher Latency**: 2-3x longer than simple prompts due to multiple round-trips
- **Reasoning Impact**: Thinking budget affects tool call generation speed
- **Streaming Benefits**: Less pronounced due to structured tool responses
- **Error Patterns**: Tool parsing failures reveal different bottlenecks

## Usage Examples

### Environment Setup
```bash
# Required for LiteLLM-based tests
export LITELLM_PROXY_API_KEY="your-api-key-here"
export LITELLM_BASE_URL="https://your-litellm-endpoint"

# Required for native Google API tests
export GEMINI_API_KEY="your-google-api-key-here"
```

### Running Tests
```bash
# Run individual test with tool calls
python test_thinking_budget.py

# Run comprehensive suite with tool calls
python run_performance_tests.py
```

## References

This architecture is based on:
- OpenHands tool calling patterns (source: OpenHands codebase)
- LiteLLM tool calling documentation (source: LiteLLM docs)
- Google Gemini function calling API (source: Google AI documentation)
- Security best practices for API key management (source: OWASP guidelines)
