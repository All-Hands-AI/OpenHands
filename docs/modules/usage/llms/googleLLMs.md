# Google Gemini/Vertex LLM Integration

This guide explains how to integrate Google's LLMs (Gemini and Vertex AI) with OpenDevin for completion tasks.

## Completion

OpenDevin uses LiteLLM for completion calls. The following resources are relevant for using OpenDevin with Google's LLMs:

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

### Gemini - Google AI Studio Configuration

To use Gemini through Google AI Studio when running the OpenDevin Docker image, set the following environment variables using `-e`:

```bash
GEMINI_API_KEY="<your-google-api-key>"
LLM_MODEL="gemini/gemini-1.5-pro"
```

### Vertex AI - Google Cloud Platform Configuration

To use Vertex AI through Google Cloud Platform when running the OpenDevin Docker image, set the following environment variables using `-e`:

```bash
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
LLM_MODEL="vertex_ai/<desired-llm-model>"
```

By configuring these settings, you'll be able to use either Google Gemini or Vertex AI services for completion tasks in OpenDevin.