# LLM Critic

The LLM Critic feature allows OpenHands to generate multiple candidate responses from the LLM and select the best one based on a critic model's evaluation. This can significantly improve the quality of the LLM's responses by filtering out low-quality or incorrect responses.

## How It Works

1. When enabled, the LLM generates multiple candidate responses (default: 8) for each request.
2. These candidates are sent to a critic model, which evaluates each response and assigns a score.
3. The response with the highest score is selected and returned.
4. The critic results and candidate responses are logged for analysis.

## Configuration

To enable the LLM Critic feature, add the following to your configuration:

```toml
[llm]
use_critic = true
critic_model = "openhands-critic-32b-v0.1-sonnet3.7-3.5-swegym-3468i-laoTrue-gamma1.0"  # Optional, defaults to the same model as the main LLM
critic_base_url = "https://your-critic-endpoint.com/pooling"  # Required
critic_api_key = "your-api-key"  # Optional, defaults to the same API key as the main LLM
critic_num_candidates = 8  # Optional, defaults to 8
```

## Parameters

- `use_critic`: Boolean flag to enable or disable the critic feature.
- `critic_model`: The model to use for the critic. If not provided, the same model as the main LLM will be used.
- `critic_api_key`: The API key to use for the critic. If not provided, the same API key as the main LLM will be used.
- `critic_base_url`: The base URL for the critic API. This is required when the critic is enabled.
- `critic_num_candidates`: The number of candidate responses to generate for the critic to evaluate. Default is 8.

## Limitations

- The critic feature is not compatible with streaming responses, as it requires generating multiple complete responses before selecting the best one.
- Using the critic increases the latency and cost of LLM requests, as it requires generating multiple responses and evaluating them.

## Example

Here's an example of how to use the LLM Critic feature in your code:

```python
from openhands.core.config import LLMConfig
from openhands.llm import LLM

# Create a configuration with the critic enabled
config = LLMConfig(
    model="claude-3-7-sonnet-20250219",
    api_key="your-api-key",
    use_critic=True,
    critic_base_url="https://your-critic-endpoint.com/pooling",
    critic_num_candidates=5
)

# Create an LLM instance with the configuration
llm = LLM(config)

# Use the LLM as usual
messages = [{"role": "user", "content": "What is the capital of France?"}]
response = llm.completion(messages=messages)

# The response will contain the critic results
print(f"Selected response: {response['choices'][0]['message']['content']}")
print(f"Critic score: {response['critic_results']['best_score']}")
```

## Logging

When the critic is enabled and `log_completions` is set to `True`, the critic results and candidate responses will be logged to the specified `log_completions_folder`. This can be useful for analyzing the performance of the critic and the quality of the candidate responses.
