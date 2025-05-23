# Groq

OpenHandsはLiteLLMを使用してGroqのチャットモデルを呼び出します。Groqをプロバイダーとして使用する方法に関するドキュメントは[こちら](https://docs.litellm.ai/docs/providers/groq)で確認できます。

## 設定

OpenHandsを実行する際、設定画面で以下の項目を設定する必要があります：
- `LLM Provider`を`Groq`に設定
- `LLM Model`を使用するモデルに設定。[Groqがホストしているモデルのリストはこちらで確認できます](https://console.groq.com/docs/models)。モデルがリストにない場合は、`Advanced`オプションを有効にして、`Custom Model`に入力してください（例：groq/&lt;model-name&gt;のように`groq/llama3-70b-8192`）。
- `API key`にGroq APIキーを設定。Groq APIキーの確認または作成については、[こちらを参照してください](https://console.groq.com/keys)。

## GroqをOpenAI互換エンドポイントとして使用する

Groqのチャット完了エンドポイントは[ほぼOpenAI互換](https://console.groq.com/docs/openai)です。そのため、OpenAI互換エンドポイントと同様にGroqモデルにアクセスできます。OpenHandsのUI設定画面で：
1. `Advanced`オプションを有効にする
2. 以下を設定する：
   - `Custom Model`に接頭辞`openai/`と使用するモデル名を組み合わせて設定（例：`openai/llama3-70b-8192`）
   - `Base URL`を`https://api.groq.com/openai/v1`に設定
   - `API Key`にGroq APIキーを設定
