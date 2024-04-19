# Azure OpenAI LLM Guide

# 1. Completion

OpenDevin uses LiteLLM for completion calls. You can find their documentation on Azure [here](https://docs.litellm.ai/docs/providers/azure)

## azure openai configs

When running the OpenDevin Docker image, you'll need to set the following environment variables using `-e`:
```
LLM_BASE_URL="<azure-api-base-url>"          # e.g. "https://openai-gpt-4-test-v-1.openai.azure.com/"
LLM_API_KEY="<azure-api-key>"
LLM_MODEL="azure/<your-gpt-deployment-name>"
LLM_API_VERSION = "<api-version>"          # e.g. "2024-02-15-preview"
```

# 2. Embeddings

OpenDevin uses llama-index for embeddings. You can find their documentation on Azure [here](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)

## azure openai configs

The model used for Azure OpenAI embeddings is "text-embedding-ada-002".
You need the correct deployment name for this model in your Azure account.

When running OpenDevin in Docker, set the following environment variables using `-e`:
```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME = "<your-embedding-deployment-name>"        # e.g. "TextEmbedding...<etc>"
LLM_API_VERSION = "<api-version>"         # e.g. "2024-02-15-preview"
```
