# OpenAI

OpenHands uses LiteLLM to make calls to OpenAI's chat models. You can find their full documentation on OpenAI chat calls [here](https://docs.litellm.ai/docs/providers/openai).

## Configuration

When running OpenHands, you'll need to set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `OpenAI`
* `LLM Model` to the model you will be using.
[Visit **here** to see a full list of OpenAI models that LiteLLM supports.](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
If the model is not in the list, toggle `Advanced Options`, and enter it in `Custom Model` (i.e. openai/&lt;model-name&gt;).
* `API Key`. To find or create your OpenAI Project API Key, [see **here**](https://platform.openai.com/api-keys).

## Using OpenAI-Compatible Endpoints

Just as for OpenAI Chat completions, we use LiteLLM for OpenAI-compatible endpoints. You can find their full documentation on this topic [here](https://docs.litellm.ai/docs/providers/openai_compatible).

## Using an OpenAI Proxy

If you're using an OpenAI proxy, you'll need to toggle `Advanced Options` in the OpenHands Settings, and set the following:
* `Custom Model` to the model you will be using, e.g. `openai/gpt-4o` or `openai/&lt;proxy_prefix&gt;/&lt;model_name&gt;`
* `API Key` to your API key.
* `Base URL` to the URL of your OpenAI proxy.
