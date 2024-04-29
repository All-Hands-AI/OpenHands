# Google Gemini/Vertex LLM

## Completion

OpenDevin uses LiteLLM for completion calls. The following resources are relevant for using OpenDevin with Google's LLMs

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

### Gemini - Google AI Studio Configs

To use Gemini through Google AI Studio when running the OpenDevin Docker image, you'll need to set the following environment variables using `-e`:

```
GEMINI_API_KEY="<your-google-api-key>"
LLM_MODEL="gemini/gemini-1.5-pro"
```

### Vertex AI - Google Cloud Platform Configs

To use Vertex AI through Google Cloud Platform when running the OpenDevin Docker image, you'll need to set the following environment variables using `-e`:

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
LLM_MODEL="vertex_ai/<desired-llm-model>"
```
