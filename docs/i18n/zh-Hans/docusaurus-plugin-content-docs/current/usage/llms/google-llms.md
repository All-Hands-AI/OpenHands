# Google Gemini/Vertex

OpenHands 使用 LiteLLM 调用 Google 的聊天模型。你可以在以下文档中找到使用 Google 作为提供商的说明：

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Gemini - Google AI Studio 配置

运行 OpenHands 时，你需要在设置中设置以下内容：
* 将 `LLM Provider` 设置为 `Gemini`
* 将 `LLM Model` 设置为你将使用的模型。
如果模型不在列表中，请切换 `Advanced Options`，并在 `Custom Model` 中输入（例如 gemini/&lt;model-name&gt; 如 `gemini/gemini-1.5-pro`）。
* 将 `API Key` 设置为你的 Gemini API 密钥

## VertexAI - Google Cloud Platform 配置

要在运行 OpenHands 时通过 Google Cloud Platform 使用 Vertex AI，你需要使用 [docker run 命令](/modules/usage/installation#start-the-app) 中的 `-e` 设置以下环境变量：

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
```

然后在设置中设置以下内容：
* 将 `LLM Provider` 设置为 `VertexAI`
* 将 `LLM Model` 设置为你将使用的模型。
如果模型不在列表中，请切换 `Advanced Options`，并在 `Custom Model` 中输入（例如 vertex_ai/&lt;model-name&gt;）。
