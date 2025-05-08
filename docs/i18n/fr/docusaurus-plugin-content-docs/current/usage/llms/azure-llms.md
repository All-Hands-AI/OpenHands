# Azure

OpenHands utilise LiteLLM pour effectuer des appels aux modèles de chat d'Azure. Vous pouvez trouver leur documentation sur l'utilisation d'Azure comme fournisseur [ici](https://docs.litellm.ai/docs/providers/azure).

## Configuration d'Azure OpenAI

Lors de l'exécution d'OpenHands, vous devrez définir la variable d'environnement suivante en utilisant `-e` dans la
[commande docker run](../installation#running-openhands) :

```
LLM_API_VERSION="<api-version>"              # ex. "2023-05-15"
```

Exemple :
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

Ensuite, dans les paramètres de l'interface OpenHands :

:::note
Vous aurez besoin du nom de déploiement ChatGPT qui peut être trouvé sur la page des déploiements dans Azure. Il est référencé comme
&lt;deployment-name&gt; ci-dessous.
:::

1. Activez les options `Advanced`.
2. Définissez les éléments suivants :
   - `Custom Model` à azure/&lt;deployment-name&gt;
   - `Base URL` à votre URL de base de l'API Azure (ex. `https://example-endpoint.openai.azure.com`)
   - `API Key` à votre clé API Azure

### Configuration d'Azure OpenAI

Lors de l'exécution d'OpenHands, définissez la variable d'environnement suivante en utilisant `-e` dans la
[commande docker run](../installation#running-openhands) :

```
LLM_API_VERSION="<api-version>"                                    # ex. "2024-02-15-preview"
```
