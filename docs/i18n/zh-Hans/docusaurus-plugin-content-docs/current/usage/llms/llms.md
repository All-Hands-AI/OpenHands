# 🤖 LLM 后端

OpenHands 可以连接到 LiteLLM 支持的任何 LLM。但是，它需要一个强大的模型才能工作。

## 模型推荐

根据我们对编码任务语言模型的评估（使用 SWE-bench 数据集），我们可以为模型选择提供一些建议。一些分析可以在[这篇比较 LLM 的博客文章](https://www.all-hands.dev/blog/evaluation-of-llms-as-coding-agents-on-swe-bench-at-30x-speed)和[这篇包含一些最新结果的博客文章](https://www.all-hands.dev/blog/openhands-codeact-21-an-open-state-of-the-art-software-development-agent)中找到。

在选择模型时，要同时考虑输出质量和相关成本。以下是调查结果的总结：

- Claude 3.5 Sonnet 是目前最好的，在 SWE-Bench Verified 上使用 OpenHands 中的默认代理可以达到 53% 的解决率。
- GPT-4o 落后于 Claude，而 o1-mini 的表现甚至比 GPT-4o 还要差一些。我们进行了一些分析，简单来说，o1 有时会"想得太多"，在可以直接完成任务的情况下执行额外的环境配置任务。
- 最后，最强大的开放模型是 Llama 3.1 405 B 和 deepseek-v2.5，它们表现得相当不错，甚至超过了一些封闭模型。

请参阅[完整文章](https://www.all-hands.dev/blog/evaluation-of-llms-as-coding-agents-on-swe-bench-at-30x-speed)了解更多详情。

根据这些发现和社区反馈，以下模型已经验证可以与 OpenHands 很好地配合使用：

- claude-3-5-sonnet（推荐）
- gpt-4 / gpt-4o
- llama-3.1-405b
- deepseek-v2.5

:::warning
OpenHands 将向您配置的 LLM 发出许多提示。这些 LLM 中的大多数都需要付费，因此请务必设置支出限制并监控使用情况。
:::

如果您已经成功地使用特定的未列出的 LLM 运行 OpenHands，请将它们添加到已验证列表中。我们也鼓励您提交 PR 分享您的设置过程，以帮助其他使用相同提供商和 LLM 的人！

有关可用提供商和模型的完整列表，请查阅 [litellm 文档](https://docs.litellm.ai/docs/providers)。

:::note
目前大多数本地和开源模型都没有那么强大。使用这些模型时，您可能会看到消息之间的长时间等待、响应不佳或有关 JSON 格式错误的错误。OpenHands 只能和驱动它的模型一样强大。但是，如果您确实找到了可以使用的模型，请将它们添加到上面的已验证列表中。
:::

## LLM 配置

以下内容可以通过设置在 OpenHands UI 中设置：

- `LLM Provider`
- `LLM Model`
- `API Key`
- `Base URL`（通过`Advanced Settings`）

有些设置可能对某些 LLM/提供商是必需的，但无法通过 UI 设置。相反，可以通过传递给 [docker run 命令](/modules/usage/installation#start-the-app)的环境变量使用 `-e` 来设置这些变量：

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
- [LiteLLM Proxy](llms/litellm-proxy)
- [OpenAI](llms/openai-llms)
- [OpenRouter](llms/openrouter)

### API 重试和速率限制

LLM 提供商通常有速率限制，有时非常低，可能需要重试。如果 OpenHands 收到速率限制错误（429 错误代码）、API 连接错误或其他瞬时错误，它将自动重试请求。

您可以根据使用的提供商的需要自定义这些选项。查看他们的文档，并设置以下环境变量来控制重试次数和重试之间的时间：

- `LLM_NUM_RETRIES`（默认为 8）
- `LLM_RETRY_MIN_WAIT`（默认为 15 秒）
- `LLM_RETRY_MAX_WAIT`（默认为 120 秒）
- `LLM_RETRY_MULTIPLIER`（默认为 2）

如果您在开发模式下运行 OpenHands，也可以在 `config.toml` 文件中设置这些选项：

```toml
[llm]
num_retries = 8
retry_min_wait = 15
retry_max_wait = 120
retry_multiplier = 2
```
