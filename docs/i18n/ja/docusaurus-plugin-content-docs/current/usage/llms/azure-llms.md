# Azure

OpenHands は LiteLLM を使用して Azure のチャットモデルを呼び出します。Azure をプロバイダとして使用する方法については、[こちら](https://docs.litellm.ai/docs/providers/azure)のドキュメントをご覧ください。

## Azure OpenAI 設定

OpenHands を実行する際には、以下の環境変数を [docker run コマンド](../installation#running-openhands) で `-e` を使用して設定する必要があります。

```
LLM_API_VERSION="<api-version>"              # 例: "2023-05-15"
```

例:
```bash
docker run -it --pull=always \
    -e LLM_API_VERSION="2023-05-15"
    ...
```

その後、OpenHands UI の設定で以下を行います。

:::note
Azure の deployments ページで ChatGPT のデプロイメント名を確認する必要があります。以下では &lt;deployment-name&gt; と表記しています。
:::

1. `Advanced` オプションを有効にします。
2. 以下を設定します:
   - `Custom Model` を azure/&lt;deployment-name&gt; に設定
   - `Base URL` を Azure API の Base URL に設定 (例: `https://example-endpoint.openai.azure.com`)
   - `API Key` を Azure API キーに設定

### Azure OpenAI 設定

OpenHands を実行する際には、以下の環境変数を [docker run コマンド](../installation#running-openhands) で `-e` を使用して設定します。

```
LLM_API_VERSION="<api-version>"                                    # 例: "2024-02-15-preview"
```
