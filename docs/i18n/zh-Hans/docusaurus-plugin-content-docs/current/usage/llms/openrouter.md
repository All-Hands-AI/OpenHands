# OpenRouter

OpenHands 使用 LiteLLM 来调用 OpenRouter 上的聊天模型。您可以在[这里](https://docs.litellm.ai/docs/providers/openrouter)找到关于使用 OpenRouter 作为提供商的文档。

## 配置

运行 OpenHands 时，您需要在 OpenHands UI 的设置中设置以下内容：
* 将 `LLM Provider` 设置为 `OpenRouter`
* 将 `LLM Model` 设置为您将使用的模型。
[访问此处查看 OpenRouter 模型的完整列表](https://openrouter.ai/models)。
如果模型不在列表中，切换到 `Advanced` 选项，并在 `Custom Model` 中输入（例如 openrouter/&lt;model-name&gt; 如 `openrouter/anthropic/claude-3.5-sonnet`）。
* 将 `API Key` 设置为您的 OpenRouter API 密钥。
