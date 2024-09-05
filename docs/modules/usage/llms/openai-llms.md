# OpenAI

OpenHands uses [LiteLLM](https://www.litellm.ai/) to make calls to OpenAI's chat models. You can find their full documentation on OpenAI chat calls [here](https://docs.litellm.ai/docs/providers/openai).

## Configuration

When running the OpenHands Docker image, you'll need to choose a model and set your API key in the OpenHands UI through the Settings.

To see a full list of OpenAI models that LiteLLM supports, please visit https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models.

To find or create your OpenAI Project API Key, please visit https://platform.openai.com/api-keys.

## Using OpenAI-Compatible Endpoints

Just as for OpenAI Chat completions, we use LiteLLM for OpenAI-compatible endpoints. You can find their full documentation on this topic [here](https://docs.litellm.ai/docs/providers/openai_compatible).

When running the OpenHands Docker image, you'll need to set the following environment variables using `-e`:

```sh
LLM_BASE_URL="<api-base-url>"   # e.g. "http://0.0.0.0:3000"
```

Then set your model and API key in the OpenHands UI through the Settings.
