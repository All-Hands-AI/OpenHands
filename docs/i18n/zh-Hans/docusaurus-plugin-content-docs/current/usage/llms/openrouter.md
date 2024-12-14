以下是翻译后的内容:

# OpenRouter

OpenHands 使用 LiteLLM 调用 OpenRouter 上的聊天模型。你可以在[这里](https://docs.litellm.ai/docs/providers/openrouter)找到他们关于使用 OpenRouter 作为提供者的文档。

## 配置

运行 OpenHands 时,你需要在设置中设置以下内容:
* `LLM Provider` 设置为 `OpenRouter`
* `LLM Model` 设置为你将使用的模型。
[访问此处查看 OpenRouter 模型的完整列表](https://openrouter.ai/models)。
如果模型不在列表中,请切换 `Advanced Options`,并在 `Custom Model` 中输入(例如 openrouter/&lt;model-name&gt; 如 `openrouter/anthropic/claude-3.5-sonnet`)。
* `API Key` 设置为你的 OpenRouter API 密钥。
