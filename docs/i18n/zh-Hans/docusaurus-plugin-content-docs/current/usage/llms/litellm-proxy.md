以下是翻译后的内容:

# LiteLLM 代理

OpenHands 支持使用 [LiteLLM 代理](https://docs.litellm.ai/docs/proxy/quick_start)来访问各种 LLM 提供商。

## 配置

要在 OpenHands 中使用 LiteLLM 代理,你需要:

1. 设置一个 LiteLLM 代理服务器(参见 [LiteLLM 文档](https://docs.litellm.ai/docs/proxy/quick_start))
2. 运行 OpenHands 时,你需要在 OpenHands UI 的设置中设置以下内容:
  * 启用`高级选项`
  * 将`自定义模型`设置为前缀 `litellm_proxy/` + 你将使用的模型(例如 `litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0`)
  * 将`Base URL`设置为你的 LiteLLM 代理 URL(例如 `https://your-litellm-proxy.com`)
  * 将`API Key`设置为你的 LiteLLM 代理 API 密钥

## 支持的模型

支持的模型取决于你的 LiteLLM 代理配置。OpenHands 支持你的 LiteLLM 代理配置的任何模型。

有关可用模型及其名称的列表,请参阅你的 LiteLLM 代理配置。
