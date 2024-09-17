# Azure

OpenHands uses LiteLLM for completion calls. You can find their documentation on Azure [here](https://docs.litellm.ai/docs/providers/azure).

## Azure OpenAI Configuration

When running OpenHands, you'll need to set the following environment variable using `-e` in the
[docker run command](/modules/usage/getting-started#installation):

```
LLM_API_VERSION="<api-version>"              # e.g. "2023-05-15"
```

Example:
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

Then set the following in the OpenHands UI through the Settings:

:::note
You will need your ChatGPT deployment name which can be found on the deployments page in Azure. This is referenced as
&lt;deployment-name&gt; below.
:::

* Enable `Advanced Options`
* `Custom Model` to azure/&lt;deployment-name&gt;
* `Base URL` to your Azure API Base URL (Example: `https://example-endpoint.openai.azure.com`)
* `API Key` to your Azure API key

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
