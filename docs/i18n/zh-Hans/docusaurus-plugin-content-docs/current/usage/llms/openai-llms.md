# OpenAI

OpenHands 使用 LiteLLM 调用 OpenAI 的聊天模型。您可以在[这里](https://docs.litellm.ai/docs/providers/openai)找到关于使用 OpenAI 作为提供商的文档。

## 配置

运行 OpenHands 时，您需要在 OpenHands UI 的设置中设置以下内容：
* `LLM Provider` 设为 `OpenAI`
* `LLM Model` 设为您将使用的模型。
[点击这里查看 LiteLLM 支持的 OpenAI 模型完整列表。](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
如果模型不在列表中，切换到`高级`选项，并在`自定义模型`中输入（例如 openai/&lt;model-name&gt; 如 `openai/gpt-4o`）。
* `API Key` 设为您的 OpenAI API 密钥。要查找或创建您的 OpenAI 项目 API 密钥，[请参见此处](https://platform.openai.com/api-keys)。

## 使用 OpenAI 兼容端点

与 OpenAI 聊天补全一样，我们使用 LiteLLM 处理 OpenAI 兼容端点。您可以在[这里](https://docs.litellm.ai/docs/providers/openai_compatible)找到他们关于此主题的完整文档。

## 使用 OpenAI 代理

如果您使用的是 OpenAI 代理，在 OpenHands UI 的设置中：
1. 启用`高级`选项
2. 设置以下内容：
   - `自定义模型`为 openai/&lt;model-name&gt;（例如 `openai/gpt-4o` 或 openai/&lt;proxy-prefix&gt;/&lt;model-name&gt;）
   - `Base URL` 设为您的 OpenAI 代理的 URL
   - `API Key` 设为您的 OpenAI API 密钥
