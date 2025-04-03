# OpenRouter

OpenHandsは、OpenRouterのチャットモデルへのAPIコールにLiteLLMを使用します。OpenRouterをプロバイダーとして使用する方法については、[こちら](https://docs.litellm.ai/docs/providers/openrouter)のドキュメントを参照してください。

## 設定

OpenHandsを実行する際、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：

* `LLMプロバイダー`を`OpenRouter`に設定
* `LLMモデル`を使用するモデルに設定。
[OpenRouterのモデルの完全なリストはこちら](https://openrouter.ai/models)を参照してください。
モデルがリストにない場合は、`詳細設定`を有効にし、`カスタムモデル`に入力してください（例：openrouter/&lt;model-name&gt;として`openrouter/anthropic/claude-3.5-sonnet`）。
* `APIキー`をOpenRouter APIキーに設定。
