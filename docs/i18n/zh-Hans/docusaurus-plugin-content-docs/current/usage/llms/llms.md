# 🤖 LLM 后端

:::note
本节适用于希望将 OpenHands 连接到不同 LLM 的用户。
:::

OpenHands 可以连接到任何 LiteLLM 支持的 LLM。但是，它需要一个强大的模型才能正常工作。

## 模型推荐

根据我们对编程任务语言模型的评估（使用 SWE-bench 数据集），我们可以提供一些模型选择建议。我们最新的基准测试结果可以在[这个电子表格](https://docs.google.com/spreadsheets/d/1wOUdFCMyY6Nt0AIqF705KN4JKOWgeI4wUGUP60krXXs/edit?gid=0)中找到。

基于这些发现和社区反馈，以下模型已被验证可以与 OpenHands 合理地配合使用：

- [anthropic/claude-3-7-sonnet-20250219](https://www.anthropic.com/api)（推荐）
- [gemini/gemini-2.5-pro](https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/)
- [deepseek/deepseek-chat](https://api-docs.deepseek.com/)
- [openai/o3-mini](https://openai.com/index/openai-o3-mini/)
- [openai/o3](https://openai.com/index/introducing-o3-and-o4-mini/)
- [openai/o4-mini](https://openai.com/index/introducing-o3-and-o4-mini/)
- [all-hands/openhands-lm-32b-v0.1](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model) -- 通过 [OpenRouter](https://openrouter.ai/all-hands/openhands-lm-32b-v0.1) 提供

:::warning
OpenHands 将向您配置的 LLM 发送许多提示。大多数这些 LLM 都需要付费，因此请确保设置支出限制并监控使用情况。
:::

如果您已成功使用列表中未包含的特定 LLM 运行 OpenHands，请将它们添加到已验证列表中。我们还鼓励您提交 PR 分享您的设置过程，以帮助使用相同提供商和 LLM 的其他人！

有关可用提供商和模型的完整列表，请参阅 [litellm 文档](https://docs.litellm.ai/docs/providers)。

:::note
大多数当前的本地和开源模型并不那么强大。使用此类模型时，您可能会看到消息之间的长时间等待、较差的响应或有关格式错误 JSON 的错误。OpenHands 的能力取决于驱动它的模型。但是，如果您确实找到了可行的模型，请将它们添加到上面的已验证列表中。
:::

## LLM 配置

以下内容可以通过 OpenHands UI 的设置进行设置：

- `LLM Provider`
- `LLM Model`
- `API Key`
- `Base URL`（通过`高级`设置）

有些设置对某些 LLM/提供商可能是必需的，但无法通过 UI 设置。相反，这些可以通过使用 `-e` 传递给 docker run 命令的环境变量来设置：

- `LLM_API_VERSION`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_DROP_PARAMS`
- `LLM_DISABLE_VISION`
- `LLM_CACHING_PROMPT`

我们有一些使用特定模型提供商运行 OpenHands 的指南：

- [Azure](llms/azure-llms)
- [Google](llms/google-llms)
- [Groq](llms/groq)
- [使用 SGLang 或 vLLM 的本地 LLM](llms/../local-llms.md)
- [LiteLLM Proxy](llms/litellm-proxy)
- [OpenAI](llms/openai-llms)
- [OpenRouter](llms/openrouter)

### API 重试和速率限制

LLM 提供商通常有速率限制，有时非常低，可能需要重试。如果 OpenHands 收到速率限制错误（429 错误代码），它将自动重试请求。

您可以根据所使用提供商的需要自定义这些选项。查看他们的文档，并设置以下环境变量来控制重试次数和重试之间的时间：

- `LLM_NUM_RETRIES`（默认为 4 次）
- `LLM_RETRY_MIN_WAIT`（默认为 5 秒）
- `LLM_RETRY_MAX_WAIT`（默认为 30 秒）
- `LLM_RETRY_MULTIPLIER`（默认为 2）

如果您在开发模式下运行 OpenHands，您也可以在 `config.toml` 文件中设置这些选项：

```toml
[llm]
num_retries = 4
retry_min_wait = 5
retry_max_wait = 30
retry_multiplier = 2
```
