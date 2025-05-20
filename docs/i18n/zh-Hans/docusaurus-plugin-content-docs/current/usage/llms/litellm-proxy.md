# LiteLLM 代理

OpenHands 支持使用 [LiteLLM 代理](https://docs.litellm.ai/docs/proxy/quick_start)来访问各种 LLM 提供商。

## 配置

要在 OpenHands 中使用 LiteLLM 代理，您需要：

1. 设置 LiteLLM 代理服务器（参见 [LiteLLM 文档](https://docs.litellm.ai/docs/proxy/quick_start)）
2. 运行 OpenHands 时，您需要通过设置在 OpenHands UI 中设置以下内容：
  * 启用 `高级` 选项
  * 将 `自定义模型` 设置为前缀 `litellm_proxy/` + 您将使用的模型（例如 `litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0`）
  * 将 `基础 URL` 设置为您的 LiteLLM 代理 URL（例如 `https://your-litellm-proxy.com`）
  * 将 `API 密钥` 设置为您的 LiteLLM 代理 API 密钥

## 支持的模型

支持的模型取决于您的 LiteLLM 代理配置。OpenHands 支持您的 LiteLLM 代理配置为处理的任何模型。

请参考您的 LiteLLM 代理配置以获取可用模型及其名称的列表。
