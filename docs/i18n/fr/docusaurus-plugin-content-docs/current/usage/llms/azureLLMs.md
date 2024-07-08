# Azure OpenAI LLM

## Complétion

OpenDevin utilise LiteLLM pour les appels de complétion. Vous pouvez trouver leur documentation sur Azure [ici](https://docs.litellm.ai/docs/providers/azure)

### Configurations openai Azure

Lors de l'exécution de l'image Docker OpenDevin, vous devrez définir les variables d'environnement suivantes en utilisant `-e` :

```
LLM_BASE_URL="<azure-api-base-url>"          # e.g. "https://openai-gpt-4-test-v-1.openai.azure.com/"
LLM_API_KEY="<azure-api-key>"
LLM_MODEL="azure/<your-gpt-deployment-name>"
LLM_API_VERSION = "<api-version>"          # e.g. "2024-02-15-preview"
```

:::note
Vous pouvez trouver le nom de votre déploiement ChatGPT sur la page des déploiements sur Azure. Par défaut ou initialement, il pourrait être le même que le nom du modèle de chat (par exemple 'GPT4-1106-preview'), mais il n'est pas obligé de l'être. Exécutez OpenDevin, et une fois chargé dans le navigateur, allez dans Paramètres et définissez le modèle comme suit : "azure/&lt;your-actual-gpt-deployment-name&gt;". Si ce n'est pas dans la liste, entrez votre propre texte et enregistrez-le.
:::

## Embeddings

OpenDevin utilise llama-index pour les embeddings. Vous pouvez trouver leur documentation sur Azure [ici](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)

### Configurations openai Azure

Le modèle utilisé pour les embeddings Azure OpenAI est "text-embedding-ada-002".
Vous avez besoin du nom de déploiement correct pour ce modèle dans votre compte Azure.

Lors de l'exécution d'OpenDevin dans Docker, définissez les variables d'environnement suivantes en utilisant `-e` :

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME = "<your-embedding-deployment-name>"        # e.g. "TextEmbedding...<etc>"
LLM_API_VERSION = "<api-version>"         # e.g. "2024-02-15-preview"
```
