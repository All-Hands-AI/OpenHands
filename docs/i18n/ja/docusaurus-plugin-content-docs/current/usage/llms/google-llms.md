# Google Gemini/Vertex

OpenHandsはLiteLLMを使用してGoogleのチャットモデルを呼び出します。Googleをプロバイダーとして使用する方法については、以下のドキュメントを参照してください：

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Gemini - Google AI Studioの設定

OpenHandsを実行する際、設定画面で以下を設定する必要があります：
- `LLM Provider`を`Gemini`に設定
- `LLM Model`を使用するモデルに設定
モデルがリストにない場合は、`Advanced`オプションを切り替えて、`Custom Model`に入力してください（例：gemini/&lt;model-name&gt;、`gemini/gemini-2.0-flash`など）。
- `API Key`にGemini APIキーを設定

## VertexAI - Google Cloud Platformの設定

Google Cloud PlatformのVertex AIを使用してOpenHandsを実行する場合、[docker runコマンド](../installation#running-openhands)で`-e`を使用して以下の環境変数を設定する必要があります：

```
GOOGLE_APPLICATION_CREDENTIALS="<gcp-サービスアカウントjsonのjsonダンプ>"
VERTEXAI_PROJECT="<あなたのgcpプロジェクトid>"
VERTEXAI_LOCATION="<あなたのgcpロケーション>"
```

その後、OpenHandsのUI設定で以下を設定します：
- `LLM Provider`を`VertexAI`に設定
- `LLM Model`を使用するモデルに設定
モデルがリストにない場合は、`Advanced`オプションを切り替えて、`Custom Model`に入力してください（例：vertex_ai/&lt;model-name&gt;）。
