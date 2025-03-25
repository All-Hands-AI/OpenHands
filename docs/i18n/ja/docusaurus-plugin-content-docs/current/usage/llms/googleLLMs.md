# Google Gemini/Vertex LLM

## Complétion

OpenHands utilise LiteLLM pour les appels de complétion. Les ressources suivantes sont pertinentes pour utiliser OpenHands avec les LLMs de Google :

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

### Configurations de Gemini - Google AI Studio

Pour utiliser Gemini via Google AI Studio lors de l'exécution de l'image Docker d'OpenHands, vous devez définir les variables d'environnement suivantes en utilisant `-e` :

```
GEMINI_API_KEY="<votre-cle-api-google>"
LLM_MODEL="gemini/gemini-1.5-pro"
```

### Configurations de Vertex AI - Google Cloud Platform

Pour utiliser Vertex AI via Google Cloud Platform lors de l'exécution de l'image Docker d'OpenHands, vous devez définir les variables d'environnement suivantes en utilisant `-e` :

```
GOOGLE_APPLICATION_CREDENTIALS="<dump-json-du-compte-de-service-gcp-json>"
VERTEXAI_PROJECT="<votre-id-de-projet-gcp>"
VERTEXAI_LOCATION="<votre-localisation-gcp>"
LLM_MODEL="vertex_ai/<modele-llm-desire>"
```
