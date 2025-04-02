# Azure OpenAI LLM

## 補完

OpenHandsはLiteLLMを使用して補完リクエストを行います。Azureに関するドキュメントは[こちら](https://docs.litellm.ai/docs/providers/azure)にあります。

### Azure OpenAI の設定

OpenHands Dockerイメージを実行する際には、以下の環境変数を `-e` を使用して設定する必要があります：

```
LLM_BASE_URL="<azure-api-base-url>"          # 例: "https://openai-gpt-4-test-v-1.openai.azure.com/"
LLM_API_KEY="<azure-api-key>"
LLM_MODEL="azure/<your-gpt-deployment-name>"
LLM_API_VERSION = "<api-version>"          # 例: "2024-02-15-preview"
```

:::note
ChatGPTデプロイメント名は、Azureのデプロイメントページで確認できます。デフォルトまたは初期状態では、チャットモデル名（例えば'GPT4-1106-preview'）と同じ場合がありますが、必ずしもそうである必要はありません。OpenHandsを実行し、ブラウザに読み込まれたら、設定に移動し、モデルを次のように設定します："azure/&lt;your-actual-gpt-deployment-name&gt;"。リストにない場合は、独自のテキストを入力して保存します。
:::

## Embeddings

OpenHandsはllama-indexを使用してembeddingsを生成します。Azureに関するドキュメントは[こちら](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/azure_openai/)にあります。

### Azure OpenAI の設定

Azure OpenAI embeddingsで使用されるモデルは "text-embedding-ada-002" です。
Azureアカウントでこのモデルの正しいデプロイメント名が必要です。

DockerでOpenHandsを実行する際には、以下の環境変数を `-e` を使用して設定してください：

```
LLM_EMBEDDING_MODEL="azureopenai"
LLM_EMBEDDING_DEPLOYMENT_NAME = "<your-embedding-deployment-name>"        # 例: "TextEmbedding...<etc>"
LLM_API_VERSION = "<api-version>"         # 例: "2024-02-15-preview"
```
