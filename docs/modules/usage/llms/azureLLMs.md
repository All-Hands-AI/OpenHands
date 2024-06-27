# Azure OpenAI LLM Integration

This guide explains how to integrate Azure OpenAI services with OpenDevin for both completion and embedding tasks.

## Completion

OpenDevin uses LiteLLM for completion calls. For detailed information, refer to the [LiteLLM Azure documentation](https://docs.litellm.ai/docs/providers/azure).

### Azure OpenAI Configuration

When running the OpenDevin Docker image, set the following environment variables using `-e`:

```bash
LLM_BASE_URL="your-azure-api-base-url"
LLM_API_KEY="your-azure-api-key"
LLM_MODEL="azure/your-gpt-deployment-name"
LLM_API_VERSION="your-api-version"
```

Note: You can find your ChatGPT deployment name on the deployments page in Azure. After running OpenDevin and loading it in the browser, go to Settings and set the model as "azure/your-actual-gpt-deployment-name".

## Embeddings

OpenDevin uses llama-index for embeddings. For more information, see the [llama-index Azure OpenAI documentation](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/).

### Azure OpenAI Embedding Configuration

The model used for Azure OpenAI embeddings is "text-embedding-ada-002". You need the correct deployment name for this model in your Azure account.

When running OpenDevin in Docker, set the following environment variables using `-e`:

```bash
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME="your-embedding-deployment-name"
LLM_API_VERSION="your-api-version"
```

By configuring these settings, you'll be able to use Azure OpenAI services for both completion and embedding tasks in OpenDevin.