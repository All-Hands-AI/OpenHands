# Google Gemini/Vertex

OpenHands 使用 LiteLLM 调用 Google 的聊天模型。您可以在以下文档中找到关于使用 Google 作为提供商的信息：

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Gemini - Google AI Studio 配置

运行 OpenHands 时，您需要在 OpenHands UI 的设置中设置以下内容：
- `LLM Provider` 设为 `Gemini`
- `LLM Model` 设为您将使用的模型。
如果列表中没有该模型，请切换到`高级`选项，并在`自定义模型`中输入（例如 gemini/&lt;model-name&gt; 如 `gemini/gemini-2.0-flash`）。
- `API Key` 设为您的 Gemini API 密钥

## VertexAI - Google Cloud Platform 配置

要通过 Google Cloud Platform 使用 Vertex AI 运行 OpenHands，您需要在 [docker run 命令](../installation#running-openhands) 中使用 `-e` 设置以下环境变量：

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
```

然后在 OpenHands UI 的设置中设置以下内容：
- `LLM Provider` 设为 `VertexAI`
- `LLM Model` 设为您将使用的模型。
如果列表中没有该模型，请切换到`高级`选项，并在`自定义模型`中输入（例如 vertex_ai/&lt;model-name&gt;）。
