# Azure

OpenHands 使用 LiteLLM 调用 Azure 的聊天模型。你可以在[这里](https://docs.litellm.ai/docs/providers/azure)找到他们关于使用 Azure 作为提供商的文档。

## Azure OpenAI 配置

运行 OpenHands 时，你需要在 [docker run 命令](/modules/usage/installation#start-the-app)中使用 `-e` 设置以下环境变量：

```
LLM_API_VERSION="<api-version>"              # 例如 "2023-05-15"
```

示例：
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

然后在 OpenHands UI 的设置中设置以下内容：

:::note
你需要你的 ChatGPT 部署名称，可以在 Azure 的部署页面找到。下面将其称为 &lt;deployment-name&gt;。
:::

* 启用 `Advanced Options`
* 将 `Custom Model` 设置为 azure/&lt;deployment-name&gt;
* 将 `Base URL` 设置为你的 Azure API 基础 URL（例如 `https://example-endpoint.openai.azure.com`）
* 将 `API Key` 设置为你的 Azure API 密钥

## Embeddings

OpenHands 使用 llama-index 进行 embeddings。你可以在[这里](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)找到他们关于 Azure 的文档。

### Azure OpenAI 配置

运行 OpenHands 时，在 [docker run 命令](/modules/usage/installation#start-the-app)中使用 `-e` 设置以下环境变量：

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME="<your-embedding-deployment-name>"   # 例如 "TextEmbedding...<etc>"
LLM_API_VERSION="<api-version>"                                    # 例如 "2024-02-15-preview"
```
