# Groq

OpenHandsは、GroqのチャットモデルへのAPIコールにLiteLLMを使用します。Groqをプロバイダーとして使用する方法については、[こちら](https://docs.litellm.ai/docs/providers/groq)のドキュメントを参照してください。

## 設定

OpenHandsを実行する際、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：
* `LLM Provider`を`Groq`に設定
* `LLM Model`を使用するモデルに設定。[Groqがホストするモデルのリストはこちら](https://console.groq.com/docs/models)を参照してください。モデルがリストにない場合は、`Advanced Options`を有効にし、`Custom Model`に入力してください（例：groq/&lt;model-name&gt;として`groq/llama3-70b-8192`）。
* `API key`をGroq APIキーに設定。Groq APIキーの確認または作成については、[こちら](https://console.groq.com/keys)を参照してください。

## OpenAI互換エンドポイントとしてのGroqの使用

Groqのチャット補完エンドポイントは[主にOpenAI互換](https://console.groq.com/docs/openai)です。そのため、他のOpenAI互換エンドポイントと同様の方法でGroqのモデルにアクセスできます。OpenHandsのUIで設定メニューから以下の項目を設定します：
* `Advanced Options`を有効にする
* `Custom Model`にプレフィックス`openai/`と使用するモデルを設定（例：`openai/llama3-70b-8192`）
* `Base URL`を`https://api.groq.com/openai/v1`に設定
* `API Key`をGroq APIキーに設定
