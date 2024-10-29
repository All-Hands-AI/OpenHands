

# Azure

OpenHands utilise LiteLLM pour faire des appels aux modèles de chat d'Azure. Vous pouvez trouver leur documentation sur l'utilisation d'Azure comme fournisseur [ici](https://docs.litellm.ai/docs/providers/azure).

## Configuration d'Azure OpenAI

Lorsque vous exécutez OpenHands, vous devrez définir la variable d'environnement suivante en utilisant `-e` dans la
[commande docker run](/modules/usage/installation#start-the-app) :

```
LLM_API_VERSION="<api-version>"              # par exemple "2023-05-15"
```

Exemple :
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

Ensuite, définissez les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :

:::note
Vous aurez besoin du nom de votre déploiement ChatGPT qui peut être trouvé sur la page des déploiements dans Azure. Il est référencé comme
&lt;deployment-name&gt; ci-dessous.
:::

* Activez `Advanced Options`
* `Custom Model` à azure/&lt;deployment-name&gt;
* `Base URL` à votre URL de base de l'API Azure (par exemple `https://example-endpoint.openai.azure.com`)
* `API Key` à votre clé API Azure

## Embeddings

OpenHands utilise llama-index pour les embeddings. Vous pouvez trouver leur documentation sur Azure [ici](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/).

### Configuration d'Azure OpenAI

Lorsque vous exécutez OpenHands, définissez les variables d'environnement suivantes en utilisant `-e` dans la
[commande docker run](/modules/usage/installation#start-the-app) :

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME="<your-embedding-deployment-name>"   # par exemple "TextEmbedding...<etc>"
LLM_API_VERSION="<api-version>"                                    # par exemple "2024-02-15-preview"
```
