# OpenAI

OpenHands 使用 LiteLLM 调用 OpenAI 的聊天模型。你可以在[这里](https://docs.litellm.ai/docs/providers/openai)找到他们关于使用 OpenAI 作为提供商的文档。

## 配置

运行 OpenHands 时，你需要在设置中设置以下内容：
* `LLM Provider` 设置为 `OpenAI`
* `LLM Model` 设置为你将使用的模型。
[访问此处查看 LiteLLM 支持的 OpenAI 模型的完整列表。](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
如果模型不在列表中，请切换 `Advanced Options`，并在 `Custom Model` 中输入它（例如 openai/&lt;model-name&gt; 如 `openai/gpt-4o`）。
* `API Key` 设置为你的 OpenAI API 密钥。要查找或创建你的 OpenAI 项目 API 密钥，[请参阅此处](https://platform.openai.com/api-keys)。

## 使用 OpenAI 兼容端点

就像 OpenAI 聊天补全一样，我们使用 LiteLLM 进行 OpenAI 兼容端点。你可以在[这里](https://docs.litellm.ai/docs/providers/openai_compatible)找到他们关于此主题的完整文档。

## 使用 OpenAI 代理

如果你使用 OpenAI 代理，你需要在设置中设置以下内容：
* 启用 `Advanced Options`
* `Custom Model` 设置为 openai/&lt;model-name&gt;（例如 `openai/gpt-4o` 或 openai/&lt;proxy-prefix&gt;/&lt;model-name&gt;）
* `Base URL` 设置为你的 OpenAI 代理的 URL
* `API Key` 设置为你的 OpenAI API 密钥
