# Groq

OpenHands 使用 LiteLLM 在 Groq 上调用聊天模型。你可以在[这里](https://docs.litellm.ai/docs/providers/groq)找到他们关于使用 Groq 作为提供商的文档。

## 配置

在运行 OpenHands 时，你需要在设置中设置以下内容：
* `LLM Provider` 设置为 `Groq`
* `LLM Model` 设置为你将使用的模型。[访问此处查看 Groq 托管的模型列表](https://console.groq.com/docs/models)。如果模型不在列表中，切换 `Advanced Options`，并在 `Custom Model` 中输入它（例如 groq/&lt;model-name&gt; 如 `groq/llama3-70b-8192`）。
* `API key` 设置为你的 Groq API 密钥。要查找或创建你的 Groq API 密钥，[请参见此处](https://console.groq.com/keys)。



## 使用 Groq 作为 OpenAI 兼容端点

Groq 的聊天完成端点[大部分与 OpenAI 兼容](https://console.groq.com/docs/openai)。因此，你可以像访问任何 OpenAI 兼容端点一样访问 Groq 模型。你可以在设置中设置以下内容：
* 启用 `Advanced Options`
* `Custom Model` 设置为前缀 `openai/` + 你将使用的模型（例如 `openai/llama3-70b-8192`）
* `Base URL` 设置为 `https://api.groq.com/openai/v1`
* `API Key` 设置为你的 Groq API 密钥
