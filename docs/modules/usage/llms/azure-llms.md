# Azure OpenAI Integration

OpenHands uses LiteLLM to make calls to Azure's chat models. You can find their documentation on using Azure as a 
provider [here](https://docs.litellm.ai/docs/providers/azure).

## Authentication Methods

OpenHands supports two authentication methods for Azure OpenAI:

### 1. API Key Authentication

When using API Key authentication, set these environment variables when running OpenHands:

```bash
# Required
LLM_API_VERSION="<api-version>"              # e.g. "2024-02-15-preview"
LLM_BASE_URL="<azure-endpoint>"              # e.g. "https://your-resource.openai.azure.com/"
LLM_API_KEY="<your-azure-api-key>"          # Your Azure OpenAI API key
LLM_MODEL="azure/<deployment-name>"          # e.g. "azure/gpt-4" where gpt-4 is your deployment name

# Optional - Only if using Azure OpenAI for embeddings
LLM_EMBEDDING_MODEL="azureopenai"            # Required for Azure OpenAI embeddings
LLM_EMBEDDING_DEPLOYMENT_NAME="<deployment>"  # Your text-embedding-ada-002 deployment name
```

Example docker run command:
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2024-02-15-preview" \
    -e LLM_BASE_URL="https://your-resource.openai.azure.com/" \
    -e LLM_API_KEY="your-api-key" \
    -e LLM_MODEL="azure/your-deployment-name" \
    docker.all-hands.dev/all-hands-ai/openhands:latest
```

### 2. Azure AD Token Authentication

For Azure AD token authentication (common in enterprise environments), use these environment variables:

```bash
# Required
LLM_API_VERSION="<api-version>"              # e.g. "2024-02-15-preview"
LLM_BASE_URL="<azure-endpoint>"              # e.g. "https://your-resource.openai.azure.com/"
AZURE_AD_TOKEN="<your-ad-token>"            # Your Azure AD access token
LLM_MODEL="azure/<deployment-name>"          # e.g. "azure/gpt-4" where gpt-4 is your deployment name

# Do not set LLM_API_KEY when using AD token authentication
```

Example docker run command with AD token:
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2024-02-15-preview" \
    -e LLM_BASE_URL="https://your-resource.openai.azure.com/" \
    -e AZURE_AD_TOKEN="your-ad-token" \
    -e LLM_MODEL="azure/your-deployment-name" \
    docker.all-hands.dev/all-hands-ai/openhands:latest
```

## UI Configuration

After starting OpenHands, configure these settings in the UI under the `LLM` tab:

1. Enable `Advanced` options
2. Set the following:
   - `LLM Provider` to `Azure`
   - `Advanced` options:
     - `Custom Model` to `azure/<deployment-name>` (same as LLM_MODEL environment variable)
     - `Base URL` to your Azure API Base URL (same as LLM_BASE_URL)
     - `API Key` to your Azure API key (only if using API key authentication)
   
   :::tip
   When using Azure AD token authentication, leave the `API Key` field empty in the UI settings.
   :::

:::note
The deployment name can be found on the Azure OpenAI Studio deployments page. By default, it may match your model name (e.g., 'gpt-4'), but you can customize it during deployment.
:::

## Troubleshooting

Common issues:
1. If using AD token authentication, make sure LLM_API_KEY is not set
2. Verify your deployment name in Azure OpenAI Studio matches what you specified in LLM_MODEL
3. Ensure the API version is current (check Azure OpenAI documentation)
4. For embeddings, the deployment must use the "text-embedding-ada-002" model
