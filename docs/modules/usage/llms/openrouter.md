# OpenRouter

OpenHands uses LiteLLM to make calls to chat models on OpenRouter. You can find their documentation on using OpenRouter as a provider [here](https://docs.litellm.ai/docs/providers/openrouter).

## Configuration

When running OpenHands, you'll need to set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `OpenRouter`
* `LLM Model` to the model you will be using.
[Visit here to see a full list of OpenRouter models](https://openrouter.ai/models).
If the model is not in the list, toggle `Advanced Options`, and enter it in `Custom Model` (e.g. openrouter/&lt;model-name&gt; like `openrouter/anthropic/claude-3.5-sonnet`).
* `API Key` to your OpenRouter API key.
