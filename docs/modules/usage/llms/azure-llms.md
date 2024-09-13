# Azure OpenAI LLM

OpenHands uses LiteLLM for completion calls. You can find their documentation on Azure [here](https://docs.litellm.ai/docs/providers/azure).

## Azure OpenAI Configuration

When running OpenHands, you'll need to set the following environment variable using `-e` in the
[docker run command](/modules/usage/getting-started#installation):

```
LLM_API_VERSION="<api-version>"              # e.g. "2024-02-15-preview"
```

Example:
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2024-02-15-preview"
    ...
```

Then set the following in the OpenHands UI through the Settings:
* `LLM Provider` to `Azure`
* `LLM Model` to the model you will be using.
[Visit **here** to see a list of Azure models that LiteLLM supports.](https://docs.litellm.ai/docs/providers/azure#azure-openai-chat-completion-models)
If the model is not in the list, toggle `Advanced Options`, and enter it in `Custom Model` (i.e. azure/&lt;model-name&gt;).
* `API Key`

:::note
You can find your ChatGPT deployment name on the deployments page in Azure.
:::

## Embeddings

OpenHands uses llama-index for embeddings. You can find their documentation on Azure [here](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/).

### Azure OpenAI Configuration

When running OpenHands, set the following environment variables using `-e` in the
[docker run command](/modules/usage/getting-started#installation):

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME="<your-embedding-deployment-name>"   # e.g. "TextEmbedding...<etc>"
LLM_API_VERSION="<api-version>"                                    # e.g. "2024-02-15-preview"
```
