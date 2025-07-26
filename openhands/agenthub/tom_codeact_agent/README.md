# TomCodeActAgent

TomCodeActAgent is an enhanced version of the CodeAct Agent that integrates with the Tom (Theory of Mind) agent to provide personalized guidance and recommendations.

## Overview

This agent extends the capabilities of CodeActAgent by adding two key integration points with the Tom agent:

1. **Instruction Improvement**: When users send requests, Tom analyzes their communication patterns and provides personalized, improved versions of the instructions
2. **Next Action Suggestions**: When tasks are completed, Tom suggests personalized next steps based on user behavior patterns and context

## Architecture

```
User Message → TomCodeActAgent → Tom Agent (propose_instructions) → Present Choices → User Decides → CodeAct Execution

Task Complete → TomCodeActAgent → Tom Agent (suggest_next_actions) → Present Suggestions → User Decides → Continue
```

## Key Features

### Tom Integration Points

#### 1. Instruction Improvement
- Triggered when a new user message is received
- Calls Tom agent's `propose_instructions` method with full conversation context
- Presents both original and improved instructions to the user
- User can choose original, improved, or edit manually

#### 2. Next Action Suggestions
- Triggered when the agent produces an `AgentFinishAction`
- Calls Tom agent's `suggest_next_actions` method with conversation context
- Presents personalized suggestions with reasoning and expected outcomes
- User decides what to do next

### Graceful Fallbacks
- Continues with normal CodeAct behavior if Tom agent is unavailable
- Configurable error handling
- No disruption to core functionality when Tom integration fails

## Configuration

### Basic Configuration

```toml
[agent.TomCodeActAgent]
enable_tom_integration = true
tom_processed_data_dir = "./data/processed_data"
tom_user_model_dir = "./data/user_model"
tom_enable_rag = true
tom_user_id = "user_123"
tom_fallback_on_error = true
tom_min_instruction_length = 5
```

### Configuration Options

- `enable_tom_integration`: Whether to enable Tom agent integration (default: false)
- `tom_processed_data_dir`: Directory for Tom agent processed data (default: "./data/processed_data")
- `tom_user_model_dir`: Directory for Tom agent user models (default: "./data/user_model")
- `tom_enable_rag`: Whether to enable RAG in Tom agent (default: true)
- `tom_user_id`: User ID for Tom agent calls (default: None, auto-generated)
- `tom_fallback_on_error`: Continue with normal behavior on Tom agent errors (default: true)
- `tom_min_instruction_length`: Minimum instruction length to trigger Tom improvement (default: 5)

## Tom Agent Integration

The agent directly creates and interacts with a Tom agent instance using the `create_tom_agent` function. All communication is in-process, with no HTTP or API calls required.

### Context Extraction

The agent extracts context from the same formatted messages that are sent to the LLM, ensuring consistency between what the agent sees and what Tom analyzes.

## User Experience

### Instruction Improvement Flow

1. User sends message: "Debug my Python application"
2. Tom analyzes and provides improvement
3. Agent presents both versions:
   ```
   🔍 Tom analyzed your request and suggests improvements:

   Original: Debug my Python application

   ✨ Improved Option 1:
   Debug the Python application by systematically adding logging statements
   and checking each variable step-by-step to identify the root cause

   💡 Why: Personalized for your preference for detailed, systematic approaches
   🎯 Confidence: 85%
   👤 Personalized for: detailed_explanations, systematic_approach

   Would you like to use the improved instruction or continue with the original?
   ```

### Next Action Suggestions Flow

1. Agent completes task (produces AgentFinishAction)
2. Tom analyzes completion and suggests next steps
3. Agent presents suggestions:
   ```
   ✅ Task completed! Tom suggests these next steps:

   1. Add logging statements to identify error location 🔴
   💭 Based on your systematic debugging approach
   📈 Expected: Clear identification of where the error occurs
   👤 Alignment: 90%

   2. Review error patterns for prevention 🟡
   💭 Helps establish long-term debugging practices
   📈 Expected: Reduced future debugging time

   What would you like to do next?
   ```

## Implementation Details

### Key Components

- `tom_codeact_agent.py`: Main agent class extending CodeActAgent
- `tom_actions.py`: Tom-specific action types
- `tom_config.py`: Configuration classes
- `prompts/system_prompt.j2`: Enhanced system prompt with Tom integration
- `README.md`: This documentation

### Integration Timing

- **Instruction Improvement**: Called in `step()` method before LLM processing when a new user message is detected
- **Next Action Suggestions**: Called in `step()` method after LLM processing when AgentFinishAction is produced

### Error Handling

- Graceful degradation when Tom agent is unavailable
- Optional strict mode (`tom_fallback_on_error=false`) for debugging
- Comprehensive logging of Tom interactions

## Development

### Testing Tom Integration

1. Ensure the Tom agent code and data directories exist:
   ```bash
   mkdir -p ./data/processed_data ./data/user_model
   ```

2. Configure OpenHands as shown above.

3. Use TomCodeActAgent in OpenHands interface.

### Debugging

- Set `DEBUG=1` to see detailed Tom agent interactions
- Check logs for Tom agent call details and responses

## Files

- `tom_codeact_agent.py`: Main agent implementation
- `tom_actions.py`: Tom-specific action types
- `tom_config.py`: Configuration classes
- `prompts/system_prompt.j2`: Enhanced system prompt with Tom integration
- `README.md`: This documentation

## Future Enhancements

- Support for user preference learning over time
- Integration with additional Tom capabilities
- Enhanced context understanding for better personalization
- Performance optimizations for Tom agent calls
