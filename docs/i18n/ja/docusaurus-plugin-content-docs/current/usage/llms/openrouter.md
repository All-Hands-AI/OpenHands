# OpenRouter

OpenHandsは、OpenRouterのチャットモデルへのAPIコールにLiteLLMを使用します。OpenRouterをプロバイダーとして使用する方法については、[こちら](https://docs.litellm.ai/docs/providers/openrouter)のドキュメントを参照してください。

## 設定

OpenHandsを実行する際、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：
* `LLM Provider`を`OpenRouter`に設定
* `LLM Model`を使用するモデルに設定。
[OpenRouterのモデルの完全なリストはこちら](https://openrouter.ai/models)を参照してください。
モデルがリストにない場合は、`Advanced Options`を有効にし、`Custom Model`に入力してください（例：openrouter/&lt;model-name&gt;として`openrouter/anthropic/claude-3.5-sonnet`）。
* `API Key`をOpenRouter APIキーに設定。
