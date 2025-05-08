# Google Gemini/Vertex

OpenHands utilise LiteLLM pour effectuer des appels aux modèles de chat de Google. Vous pouvez consulter leur documentation sur l'utilisation de Google comme fournisseur :

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Configurations Gemini - Google AI Studio

Lors de l'exécution d'OpenHands, vous devrez définir les éléments suivants dans l'interface utilisateur d'OpenHands via les Paramètres :
- `LLM Provider` sur `Gemini`
- `LLM Model` sur le modèle que vous utiliserez.
Si le modèle n'est pas dans la liste, activez les options `Advanced`, et saisissez-le dans `Custom Model` (par exemple gemini/&lt;nom-du-modèle&gt; comme `gemini/gemini-2.0-flash`).
- `API Key` avec votre clé API Gemini

## Configurations VertexAI - Google Cloud Platform

Pour utiliser Vertex AI via Google Cloud Platform lors de l'exécution d'OpenHands, vous devrez définir les variables d'environnement suivantes en utilisant `-e` dans la [commande docker run](../installation#running-openhands) :

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-du-compte-de-service-gcp-json>"
VERTEXAI_PROJECT="<votre-id-de-projet-gcp>"
VERTEXAI_LOCATION="<votre-emplacement-gcp>"
```

Ensuite, définissez les éléments suivants dans l'interface utilisateur d'OpenHands via les Paramètres :
- `LLM Provider` sur `VertexAI`
- `LLM Model` sur le modèle que vous utiliserez.
Si le modèle n'est pas dans la liste, activez les options `Advanced`, et saisissez-le dans `Custom Model` (par exemple vertex_ai/&lt;nom-du-modèle&gt;).
