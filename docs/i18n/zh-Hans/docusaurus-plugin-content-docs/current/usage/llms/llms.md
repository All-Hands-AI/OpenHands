---
sidebar_position: 2
---

# 🤖 LLM 支持

OpenHands 可以兼容任何 LLM 后端。
关于所有可用 LM 提供商和模型的完整列表，请参阅
[litellm 文档](https://docs.litellm.ai/docs/providers)。

:::warning
OpenHands 将向你配置的 LLM 发出许多提示。大多数这些 LLM 都是收费的——请务必设定支出限额并监控使用情况。
:::

`LLM_MODEL` 环境变量控制在编程交互中使用的模型。
但在使用 OpenHands UI 时，你需要在设置窗口中选择你的模型（左下角的齿轮）。

某些 LLM 可能需要以下环境变量：

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_API_VERSION`

我们有一些指南，介绍了如何使用特定模型提供商运行 OpenHands：

- [ollama](llms/local-llms)
- [Azure](llms/azure-llms)

如果你使用其他提供商，我们鼓励你打开一个 PR 来分享你的配置！

## 关于替代模型的注意事项

最好的模型是 GPT-4 和 Claude 3。目前的本地和开源模型
远没有那么强大。当使用替代模型时，
你可能会看到信息之间的长时间等待，
糟糕的响应，或关于 JSON格式错误的错误。OpenHands
的强大程度依赖于其驱动的模型——幸运的是，我们团队的人员
正在积极致力于构建更好的开源模型！

## API 重试和速率限制

一些 LLM 有速率限制，可能需要重试操作。OpenHands 会在收到 429 错误或 API 连接错误时自动重试请求。
你可以设置 `LLM_NUM_RETRIES`，`LLM_RETRY_MIN_WAIT`，`LLM_RETRY_MAX_WAIT` 环境变量来控制重试次数和重试之间的时间。
默认情况下，`LLM_NUM_RETRIES` 为 5，`LLM_RETRY_MIN_WAIT` 和 `LLM_RETRY_MAX_WAIT` 分别为 3 秒和 60 秒。
