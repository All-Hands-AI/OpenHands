---
sidebar_position: 3
---

# 🤖 LLM Backends

OpenHands can connect to any LLM supported by LiteLLM. However, it requires a powerful model to work.
The following are verified by the community to work with OpenHands:

* claude-3-5-sonnet
* gemini-1.5-pro / gemini-1.5-flash
* gpt-4 / gpt-4o
* llama-3.1-405b / hermes-3-llama-3.1-405b
* wizardlm-2-8x22b

:::warning
OpenHands will issue many prompts to the LLM you configure. Most of these LLMs cost money, so be sure to set spending
limits and monitor usage.
:::

If you have successfully run OpenHands with specific LLMs not in the list, please add them to the verified list. We
also encourage you to open a PR to share your setup process to help others using the same provider and LLM!

For a full list of the providers and models available, please consult the
[litellm documentation](https://docs.litellm.ai/docs/providers).

:::note
Most current local and open source models are not as powerful. When using such models, you may see long
wait times between messages, poor responses, or errors about malformed JSON. OpenHands can only be as powerful as the
models driving it. However, if you do find ones that work, please add them to the verified list above.
:::

## LLM Configuration

The following can be set in the OpenHands UI through the Settings:
* `LLM Provider`
* `LLM Model`
* `API Key`
* `Base URL` (through `Advanced Settings`)

There are some settings that may be necessary for some LLMs/providers that cannot be set through the UI. Instead, these
can be set through environment variables passed to the [docker run command](/modules/usage/getting-started#installation)
using `-e`:

* `LLM_API_VERSION`
* `LLM_EMBEDDING_MODEL`
* `LLM_EMBEDDING_DEPLOYMENT_NAME`
* `LLM_DROP_PARAMS`
* `LLM_DISABLE_VISION`
* `LLM_CACHING_PROMPT`

We have a few guides for running OpenHands with specific model providers:

* [Azure](llms/azure-llms)
* [Google](llms/google-llms)
* [Groq](llms/groq)
* [ollama](llms/local-llms)
* [OpenAI](llms/openai-llms)

### API retries and rate limits

Some LLMs have rate limits and may require retries. OpenHands will automatically retry requests if it receives a 429 error or API connection error.
You can set the following environment variables to control the number of retries and the time between retries:

* `LLM_NUM_RETRIES` (Default of 8)
* `LLM_RETRY_MIN_WAIT` (Default of 15 seconds)
* `LLM_RETRY_MAX_WAIT` (Default of 120 seconds)
