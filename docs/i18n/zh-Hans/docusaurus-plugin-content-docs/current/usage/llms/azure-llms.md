# Azure

OpenHands 使用 LiteLLM 来调用 Azure 的聊天模型。您可以在[这里](https://docs.litellm.ai/docs/providers/azure)找到他们关于使用 Azure 作为提供商的文档。

## Azure OpenAI 配置

运行 OpenHands 时，您需要使用 [docker run 命令](../installation#running-openhands)中的 `-e` 设置以下环境变量：

```
LLM_API_VERSION="<api-version>"              # 例如 "2023-05-15"
```

示例：
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

然后在 OpenHands UI 设置中：

:::note
您需要您的 ChatGPT 部署名称，可以在 Azure 的部署页面上找到。这在下面被引用为 &lt;deployment-name&gt;。
:::

1. 启用 `高级` 选项。
2. 设置以下内容：
   - `自定义模型` 设为 azure/&lt;deployment-name&gt;
   - `基础 URL` 设为您的 Azure API 基础 URL（例如 `https://example-endpoint.openai.azure.com`）
   - `API 密钥` 设为您的 Azure API 密钥

### Azure OpenAI 配置

运行 OpenHands 时，使用 [docker run 命令](../installation#running-openhands)中的 `-e` 设置以下环境变量：

```
LLM_API_VERSION="<api-version>"                                    # 例如 "2024-02-15-preview"
```
