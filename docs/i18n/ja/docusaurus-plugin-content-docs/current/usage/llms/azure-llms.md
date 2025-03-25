# Azure

OpenHandsは、AzureのチャットモデルへのAPIコールにLiteLLMを使用します。Azureをプロバイダーとして使用する方法については、[こちら](https://docs.litellm.ai/docs/providers/azure)のドキュメントを参照してください。

## Azure OpenAIの設定

OpenHandsを実行する際、[docker runコマンド](/modules/usage/installation#start-the-app)で`-e`を使用して以下の環境変数を設定する必要があります：

```
LLM_API_VERSION="<api-version>"              # 例："2023-05-15"
```

例：
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

次に、OpenHandsのUIで設定メニューから以下の項目を設定します：

:::note
AzureのデプロイメントページにあるChatGPTデプロイメント名が必要です。これは以下で
&lt;deployment-name&gt;として参照されています。
:::

* `Advanced Options`を有効にする
* `Custom Model`を`azure/<deployment-name>`に設定
* `Base URL`をAzure APIのベースURL（例：`https://example-endpoint.openai.azure.com`）に設定
* `API Key`をAzure APIキーに設定

## 埋め込み（Embeddings）

OpenHandsは埋め込みにllama-indexを使用します。Azureに関するドキュメントは[こちら](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)を参照してください。

### Azure OpenAIの設定

OpenHandsを実行する際、[docker runコマンド](/modules/usage/installation#start-the-app)で`-e`を使用して以下の環境変数を設定します：

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME="<your-embedding-deployment-name>"   # 例："TextEmbedding...<etc>"
LLM_API_VERSION="<api-version>"                                    # 例："2024-02-15-preview"
```
