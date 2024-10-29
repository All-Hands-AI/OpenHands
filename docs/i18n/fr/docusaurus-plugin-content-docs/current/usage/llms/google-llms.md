

# Google Gemini/Vertex

OpenHands utilise LiteLLM pour faire des appels aux modèles de chat de Google. Vous pouvez trouver leur documentation sur l'utilisation de Google comme fournisseur :

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Configurations de Gemini - Google AI Studio

Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
* `LLM Provider` à `Gemini`
* `LLM Model` au modèle que vous utiliserez.
Si le modèle ne figure pas dans la liste, activez `Advanced Options` et entrez-le dans `Custom Model` (par exemple, gemini/&lt;model-name&gt; comme `gemini/gemini-1.5-pro`).
* `API Key` à votre clé API Gemini

## Configurations de VertexAI - Google Cloud Platform

Pour utiliser Vertex AI via Google Cloud Platform lors de l'exécution d'OpenHands, vous devrez définir les variables d'environnement suivantes en utilisant `-e` dans la [commande docker run](/modules/usage/installation#start-the-app) :

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
```

Ensuite, définissez les éléments suivants dans l'interface utilisateur d'OpenHands via les paramètres :
* `LLM Provider` à `VertexAI`
* `LLM Model` au modèle que vous utiliserez.
Si le modèle ne figure pas dans la liste, activez `Advanced Options` et entrez-le dans `Custom Model` (par exemple, vertex_ai/&lt;model-name&gt;).
