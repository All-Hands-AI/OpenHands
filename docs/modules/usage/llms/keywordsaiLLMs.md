# Keywords AI LLM

:::info
[Keywords AI](https://keywordsai.co/) is a unified developer platform where you can call 150+ LLM using the OpenAI format with one API key and get insights into your AI products. With 2 lines of code, you can build better AI products with complete observability.
:::

## Completion

OpenDevin uses LiteLLM for completion calls. You can find their documentation on Custom API Server [here](https://docs.litellm.ai/docs/providers/custom_openai_proxy)

### Keywords AI configs

When running the OpenDevin Docker image, you'll need to set the following environment variables using `-e`:

```
LLM_BASE_URL="https://api.keywordsai.co/api/"
LLM_API_KEY="<keywords-ai-api-key>"
LLM_MODEL="<keywords-ai-model-name>"
```
:::tip
The full list of supported models by Keywords AI can be found in the [page](https://platform.keywordsai.co/platform/models).
:::

You can refer to the [Quick Start](https://docs.keywordsai.co/get-started/quick-start) for more details.
