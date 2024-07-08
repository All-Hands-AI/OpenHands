# Google Gemini/Vertex LLM

## Completion

OpenDevin 使用 LiteLLM 进行补全调用。以下资源与使用 OpenDevin 和 Google 的 LLM 相关：

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

### Gemini - Google AI Studio 配置

在运行 OpenDevin Docker 镜像时，通过 Google AI Studio 使用 Gemini，你需要使用 `-e` 设置以下环境变量：

```
GEMINI_API_KEY="<your-google-api-key>"
LLM_MODEL="gemini/gemini-1.5-pro"
```

### Vertex AI - Google Cloud Platform 配置

在运行 OpenDevin Docker 镜像时，通过 Google Cloud Platform 使用 Vertex AI，你需要使用 `-e` 设置以下环境变量：

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
LLM_MODEL="vertex_ai/<desired-llm-model>"
```
