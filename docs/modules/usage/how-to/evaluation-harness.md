# Evaluation

This guide provides an overview of how to integrate your own evaluation benchmark into the OpenHands framework.

## Setup Environment and LLM Configuration

Please follow instructions [here](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) to setup your local development environment.
OpenHands in development mode uses `config.toml` to keep track of most configurations.

Here's an example configuration file you can use to define and use multiple LLMs:




```toml
[llm]
# IMPORTANT: add your API key here, and set the model to the one you want to evaluate
model = "claude-3-5-sonnet-20241022"
api_key = "sk-XXX"

[llm.eval_gpt4_1106_preview_llm]
model = "gpt-4-1106-preview"
api_key = "XXX"
temperature = 0.0

[llm.eval_some_openai_compatible_model_llm]
model = "openai/MODEL_NAME"
base_url = "https://OPENAI_COMPATIBLE_URL/v1"
api_key = "XXX"
temperature = 0.0
```

