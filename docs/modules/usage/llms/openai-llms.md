# OpenAI

OpenHands uses LiteLLM to make calls to OpenAI's chat models. You can find their documentation on using OpenAI as a provider [here](https://docs.litellm.ai/docs/providers/openai).

## Configuration

When running OpenHands, you'll need to set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `OpenAI`
* `LLM Model` to the model you will be using.
[Visit here to see a full list of OpenAI models that LiteLLM supports.](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
If the model is not in the list, toggle `Advanced Options`, and enter it in `Custom Model` (e.g. openai/&lt;model-name&gt; like `openai/gpt-4o`).
* `API Key` to your OpenAI API key. To find or create your OpenAI Project API Key, [see here](https://platform.openai.com/api-keys).

## Using OpenAI-Compatible Endpoints

Just as for OpenAI Chat completions, we use LiteLLM for OpenAI-compatible endpoints. You can find their full documentation on this topic [here](https://docs.litellm.ai/docs/providers/openai_compatible).

## Using an OpenAI Proxy

If you're using an OpenAI proxy, in the OpenHands UI through the Settings:
1. Enable `Advanced Options`
2. Set the following:
   - `Custom Model` to openai/&lt;model-name&gt; (e.g. `openai/gpt-4o` or openai/&lt;proxy-prefix&gt;/&lt;model-name&gt;)
   - `Base URL` to the URL of your OpenAI proxy
   - `API Key` to your OpenAI API key
