# OpenHands Experiment Manager

The Experiment Manager allows for running experiments and A/B tests in OpenHands, enabling customization of various components including system prompts, agent configurations, and more.

## Agent Experiment Manager

The `AgentExperimentManager` allows you to customize the system prompt used by agents in OpenHands. This is particularly useful for:

- Testing different system prompts to improve agent performance
- Specializing agents for specific tasks
- Running A/B tests to compare different prompt variations

### Usage

#### Setting a Custom System Prompt via Environment Variable

The simplest way to use a custom system prompt is to set the `OPENHANDS_SYSTEM_PROMPT_FILENAME` environment variable:

```bash
export OPENHANDS_SYSTEM_PROMPT_FILENAME=my_custom_prompt.j2
```

This will cause all new conversations to use the specified system prompt file instead of the default `system_prompt.j2`.

#### Creating Custom Prompt Files

1. Create your custom prompt file in the agent's prompts directory (e.g., `/openhands/agenthub/codeact_agent/prompts/my_custom_prompt.j2`)
2. Set the environment variable to point to your custom prompt file
3. Start OpenHands

#### Example: Creating a Specialized Agent for Code Review

1. Create a file named `code_review_prompt.j2` in the CodeActAgent's prompts directory
2. Add specialized instructions for code review in the prompt template
3. Set the environment variable:
   ```bash
   export OPENHANDS_SYSTEM_PROMPT_FILENAME=code_review_prompt.j2
   ```
4. Start OpenHands

### Advanced Usage: A/B Testing

The `AgentExperimentManager` includes commented code that demonstrates how to implement A/B testing based on conversation IDs. This can be extended to create more sophisticated experiment designs.

To implement A/B testing:

1. Uncomment and modify the A/B testing code in `agent_experiment_manager.py`
2. Create multiple system prompt files for different experiment groups
3. The experiment manager will automatically assign conversations to different groups based on the conversation ID

### Extending the Experiment Manager

You can extend the `AgentExperimentManager` to implement more complex experiment designs:

- Multi-variant testing (A/B/C/D testing)
- User-based experiments
- Time-based experiments
- Feature flag experiments

To create your own experiment manager implementation:

1. Create a new class that inherits from `ExperimentManager`
2. Override the `run_conversation_variant_test` method
3. Set the `OPENHANDS_EXPERIMENT_MANAGER_CLS` environment variable to point to your implementation

```python
# Example custom experiment manager
class MyCustomExperimentManager(ExperimentManager):
    @staticmethod
    def run_conversation_variant_test(
        user_id: str, conversation_id: str, conversation_settings: ConversationInitData
    ) -> ConversationInitData:
        # Your custom experiment logic here
        return modified_settings
```

```bash
export OPENHANDS_EXPERIMENT_MANAGER_CLS=my_module.MyCustomExperimentManager
```
