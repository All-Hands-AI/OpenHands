# Azure OpenAI 大型语言模型

## 完成

OpenDevin 使用 LiteLLM 进行完成调用。你可以在 Azure 的文档中找到他们的文档 [这里](https://docs.litellm.ai/docs/providers/azure)

### Azure openai 配置

在运行 OpenDevin Docker 镜像时，你需要使用 `-e` 设置以下环境变量：

```
LLM_BASE_URL="<azure-api-base-url>"          # 示例: "https://openai-gpt-4-test-v-1.openai.azure.com/"
LLM_API_KEY="<azure-api-key>"
LLM_MODEL="azure/<your-gpt-deployment-name>"
LLM_API_VERSION = "<api-version>"          # 示例: "2024-02-15-preview"
```

:::note
你可以在 Azure 的部署页面找到你的 ChatGPT 部署名称。它可能与默认或最初设置的聊天模型名称相同（例如 'GPT4-1106-preview'），但不一定相同。运行 OpenDevin，当你在浏览器中加载它时，进入设置并按照上述方式设置模型: "azure/&lt;your-actual-gpt-deployment-name&gt;"。如果列表中没有，请输入你自己的文本并保存。
:::

## 嵌入

OpenDevin 使用 llama-index 进行嵌入。你可以在 Azure 的文档中找到他们的文档 [这里](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)

### Azure openai 配置

Azure OpenAI 嵌入使用的模型是 "text-embedding-ada-002"。
你需要在你的 Azure 账户中为这个模型设置正确的部署名称。

在 Docker 中运行 OpenDevin 时，使用 `-e` 设置以下环境变量：

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME = "<your-embedding-deployment-name>"        # 示例: "TextEmbedding...<etc>"
LLM_API_VERSION = "<api-version>"         # 示例: "2024-02-15-preview"
```
