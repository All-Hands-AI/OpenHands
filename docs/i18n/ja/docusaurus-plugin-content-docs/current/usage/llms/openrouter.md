# OpenRouter

OpenHandsはLiteLLMを使用してOpenRouter上のチャットモデルを呼び出します。OpenRouterをプロバイダーとして使用する方法に関するドキュメントは[こちら](https://docs.litellm.ai/docs/providers/openrouter)で確認できます。

## 設定

OpenHandsを実行する際、設定画面から以下の項目を設定する必要があります：
* `LLM Provider`を`OpenRouter`に設定
* `LLM Model`を使用するモデルに設定
[OpenRouterモデルの完全なリストはこちらで確認できます](https://openrouter.ai/models)。
モデルがリストにない場合は、`Advanced`オプションを切り替えて、`Custom Model`に入力してください（例：openrouter/&lt;model-name&gt; のように `openrouter/anthropic/claude-3.5-sonnet`）。
* `API Key`にOpenRouterのAPIキーを設定
