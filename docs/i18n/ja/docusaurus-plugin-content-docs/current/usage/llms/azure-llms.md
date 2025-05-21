# Azure

OpenHandsはLiteLLMを使用してAzureのチャットモデルを呼び出します。Azureをプロバイダーとして使用する方法に関するドキュメントは[こちら](https://docs.litellm.ai/docs/providers/azure)で確認できます。

## Azure OpenAI設定

OpenHandsを実行する際、[docker runコマンド](../installation#running-openhands)で`-e`を使用して以下の環境変数を設定する必要があります：

```
LLM_API_VERSION="<api-version>"              # 例: "2023-05-15"
```

例：
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

その後、OpenHands UIの設定で：

:::note
Azureのデプロイメントページで確認できるChatGPTデプロイメント名が必要です。これは以下の&lt;deployment-name&gt;として参照されます。
:::

1. `Advanced`オプションを有効にします。
2. 以下を設定します：
   - `Custom Model`を azure/&lt;deployment-name&gt; に設定
   - `Base URL`を Azure API ベースURL（例：`https://example-endpoint.openai.azure.com`）に設定
   - `API Key`を Azure APIキーに設定

### Azure OpenAI設定

OpenHandsを実行する際、[docker runコマンド](../installation#running-openhands)で`-e`を使用して以下の環境変数を設定します：

```
LLM_API_VERSION="<api-version>"                                    # 例: "2024-02-15-preview"
```
