# Google Gemini/Vertex LLM

## 補完

OpenHandsはLiteLLMを使用して補完リクエストを行います。以下のリソースは、OpenHandsをGoogleのLLMと一緒に使用する際に関連があります。

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

### Gemini - Google AI Studioの設定

OpenHandsのDockerイメージを実行する際にGoogle AI Studio経由でGeminiを使用するには、以下の環境変数を`-e`を使って設定する必要があります。

```
GEMINI_API_KEY="<your-google-api-key>"
LLM_MODEL="gemini/gemini-1.5-pro"
```

### Vertex AI - Google Cloud Platformの設定

OpenHandsのDockerイメージを実行する際にGoogle Cloud Platform経由でVertex AIを使用するには、以下の環境変数を`-e`を使って設定する必要があります。

```
GOOGLE_APPLICATION_CREDENTIALS="<gcp-service-account-json-dump>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
LLM_MODEL="vertex_ai/<desired-llm-model>"
```
