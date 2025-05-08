# Groq

OpenHands 使用 LiteLLM 调用 Groq 上的聊天模型。您可以在[这里](https://docs.litellm.ai/docs/providers/groq)找到关于使用 Groq 作为提供商的文档。

## 配置

运行 OpenHands 时，您需要在 OpenHands UI 的设置中设置以下内容：
- `LLM Provider` 设为 `Groq`
- `LLM Model` 设为您将使用的模型。[访问此处查看 Groq 托管的模型列表](https://console.groq.com/docs/models)。如果模型不在列表中，切换到`高级`选项，并在`自定义模型`中输入（例如 groq/&lt;model-name&gt; 如 `groq/llama3-70b-8192`）。
- `API key` 设为您的 Groq API 密钥。要查找或创建您的 Groq API 密钥，[请参见此处](https://console.groq.com/keys)。

## 使用 Groq 作为 OpenAI 兼容端点

Groq 的聊天完成端点[大部分与 OpenAI 兼容](https://console.groq.com/docs/openai)。因此，您可以像访问任何 OpenAI 兼容端点一样访问 Groq 模型。在 OpenHands UI 的设置中：
1. 启用`高级`选项
2. 设置以下内容：
   - `自定义模型`设为前缀 `openai/` + 您将使用的模型（例如 `openai/llama3-70b-8192`）
   - `Base URL` 设为 `https://api.groq.com/openai/v1`
   - `API Key` 设为您的 Groq API 密钥
