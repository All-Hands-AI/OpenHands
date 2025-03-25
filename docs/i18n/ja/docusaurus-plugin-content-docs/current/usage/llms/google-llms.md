# Google Gemini/Vertex

OpenHandsは、GoogleのチャットモデルへのAPIコールにLiteLLMを使用します。Googleをプロバイダーとして使用する方法については、以下のドキュメントを参照してください：

- [Gemini - Google AI Studio](https://docs.litellm.ai/docs/providers/gemini)
- [VertexAI - Google Cloud Platform](https://docs.litellm.ai/docs/providers/vertex)

## Gemini - Google AI Studioの設定

OpenHandsを実行する際、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：
* `LLM Provider`を`Gemini`に設定
* `LLM Model`を使用するモデルに設定。
モデルがリストにない場合は、`Advanced Options`を有効にし、`Custom Model`に入力してください（例：gemini/&lt;model-name&gt;として`gemini/gemini-1.5-pro`）。
* `API Key`をGemini APIキーに設定

## VertexAI - Google Cloud Platformの設定

Google Cloud PlatformのVertex AIを使用してOpenHandsを実行する際、[docker runコマンド](/modules/usage/installation#start-the-app)で`-e`を使用して以下の環境変数を設定する必要があります：

```
GOOGLE_APPLICATION_CREDENTIALS="<json-dump-of-gcp-service-account-json>"
VERTEXAI_PROJECT="<your-gcp-project-id>"
VERTEXAI_LOCATION="<your-gcp-location>"
```

次に、OpenHandsのUIで設定メニューから以下の項目を設定します：
* `LLM Provider`を`VertexAI`に設定
* `LLM Model`を使用するモデルに設定。
モデルがリストにない場合は、`Advanced Options`を有効にし、`Custom Model`に入力してください（例：vertex_ai/&lt;model-name&gt;）。
