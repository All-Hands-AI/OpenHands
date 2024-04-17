# Azure OpenAI LLM Guide

# 1. Completion

OpenDevin uses LiteLLM for completion calls. You can find their documentation on Azure [here](https://docs.litellm.ai/docs/providers/azure)

## azure openai configs

During installation of OpenDevin, you can set up the following parameters:
```
LLM_BASE_URL="<azure-api-base-url>"          # e.g. "https://openai-gpt-4-test-v-1.openai.azure.com/"
LLM_API_KEY="<azure-api-key>"
LLM_MODEL="azure/<your-gpt-deployment-name>"
```

They will be saved in the `config.toml` file in the `OpenDevin` directory. You can add or edit them manually in the file after installation.

In addition, you need to set the following environment variable, which is used by the LiteLLM library to make requests to the Azure API:

`AZURE_API_VERSION = "<api-version>"          # e.g. "2024-02-15-preview"`

You can set the environment variable in your terminal or in an `.env` file in the `OpenDevin` directory.

Alternatively, you can add all these in .env, however in that case make sure to check the LiteLLM documentation for the correct variables.

# 2. Embeddings

OpenDevin uses llama-index for embeddings. You can find their documentation on Azure [here](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)

## azure openai configs

The model used for Azure OpenAI embeddings is "text-embedding-ada-002". You need the correct deployment name for this model in your Azure account.

During installation of OpenDevin, you can set the following parameters used for embeddings, when prompted by the makefile:

```
LLM_EMBEDDING_MODEL="azureopenai"
DEPLOYMENT_NAME = "<your-embedding-deployment-name>"        # e.g. "TextEmbedding...<etc>"
LLM_API_VERSION = "<api-version>"         # e.g. "2024-02-15-preview"
```

You can re-run ```make setup-config``` anytime, or add or edit them manually in the file afterwards.
