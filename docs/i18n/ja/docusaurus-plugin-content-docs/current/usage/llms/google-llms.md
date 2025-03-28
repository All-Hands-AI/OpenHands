以下は、指定されたコンテンツの日本語訳です。

# Google Gemini/Vertex

OpenHandsはLiteLLMを使用して、Googleのチャットモデルを呼び出します。Googleをプロバイダとして使用する方法については、以下のドキュメントを参照してください。

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Gemini - Google AI Studio の設定

OpenHandsを実行する際、設定画面で以下を設定する必要があります。
- `LLM Provider` を `Gemini` に設定
- `LLM Model` を使用するモデルに設定
モデルがリストにない場合は、`Advanced` オプションを切り替えて、`Custom Model` に入力します（例: `gemini/gemini-2.0-flash` のように gemini/&lt;model-name&gt;）。
- `API Key` を Gemini API キーに設定

## VertexAI - Google Cloud Platform の設定

Google Cloud Platform 経由で Vertex AI を使用して OpenHands を実行するには、[docker run コマンド](../installation#running-openhands)で `-e` を使用して以下の環境変数を設定する必要があります。

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
```

その後、設定画面で以下を設定します。
- `LLM Provider` を `VertexAI` に設定
- `LLM Model` を使用するモデルに設定
モデルがリストにない場合は、`Advanced` オプションを切り替えて、`Custom Model` に入力します（例: vertex_ai/&lt;model-name&gt;）。
