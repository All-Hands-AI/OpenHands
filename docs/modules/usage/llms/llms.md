# 🤖 LLM Backends

OpenHands can connect to any LLM supported by LiteLLM. However, it requires a powerful model to work.

## Model Recommendations

Based on our evaluations of language models for coding tasks (using the SWE-bench dataset), we can provide some
recommendations for model selection. Some analyses can be found in [this blog article comparing LLMs](https://www.all-hands.dev/blog/evaluation-of-llms-as-coding-agents-on-swe-bench-at-30x-speed) and
[this blog article with some more recent results](https://www.all-hands.dev/blog/openhands-codeact-21-an-open-state-of-the-art-software-development-agent).

When choosing a model, consider both the quality of outputs and the associated costs. Here's a summary of the findings:

- Claude 3.5 Sonnet is the best by a fair amount, achieving a 53% resolve rate on SWE-Bench Verified with the default agent in OpenHands.
- GPT-4o lags behind, and o1-mini actually performed somewhat worse than GPT-4o. We went in and analyzed the results a little, and briefly it seemed like o1 was sometimes "overthinking" things, performing extra environment configuration tasks when it could just go ahead and finish the task.
- Finally, the strongest open models were Llama 3.1 405 B and deepseek-v2.5, and they performed reasonably, even besting some of the closed models.

Please refer to the [full article](https://www.all-hands.dev/blog/evaluation-of-llms-as-coding-agents-on-swe-bench-at-30x-speed) for more details.

Based on these findings and community feedback, the following models have been verified to work reasonably well with OpenHands:

- claude-3-5-sonnet (recommended)
- gpt-4 / gpt-4o
- llama-3.1-405b
- deepseek-v2.5

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

- `LLM Provider`
- `LLM Model`
- `API Key`
- `Base URL` (through `Advanced Settings`)

There are some settings that may be necessary for some LLMs/providers that cannot be set through the UI. Instead, these
can be set through environment variables passed to the [docker run command](/modules/usage/installation#start-the-app)
using `-e`:

- `LLM_API_VERSION`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_DROP_PARAMS`
- `LLM_DISABLE_VISION`
- `LLM_CACHING_PROMPT`

We have a few guides for running OpenHands with specific model providers:

- [Azure](llms/azure-llms)
- [Google](llms/google-llms)
- [Groq](llms/groq)
- [LiteLLM Proxy](llms/litellm-proxy)
- [OpenAI](llms/openai-llms)
- [OpenRouter](llms/openrouter)

### API retries and rate limits

LLM providers typically have rate limits, sometimes very low, and may require retries. OpenHands will automatically
retry requests if it receives a Rate Limit Error (429 error code), API connection error, or other transient errors.

You can customize these options as you need for the provider you're using. Check their documentation, and set the
following environment variables to control the number of retries and the time between retries:

- `LLM_NUM_RETRIES` (Default of 8)
- `LLM_RETRY_MIN_WAIT` (Default of 15 seconds)
- `LLM_RETRY_MAX_WAIT` (Default of 120 seconds)
- `LLM_RETRY_MULTIPLIER` (Default of 2)

If you are running OpenHands in development mode, you can also set these options in the `config.toml` file:

```toml
[llm]
num_retries = 8
retry_min_wait = 15
retry_max_wait = 120
retry_multiplier = 2
```
