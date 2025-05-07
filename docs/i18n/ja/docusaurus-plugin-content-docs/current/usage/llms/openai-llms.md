# OpenAI

OpenHandsはLiteLLMを使用してOpenAIのチャットモデルを呼び出します。OpenAIをプロバイダーとして使用する方法に関するドキュメントは[こちら](https://docs.litellm.ai/docs/providers/openai)で確認できます。

## 設定

OpenHandsを実行する際、設定画面で以下の項目を設定する必要があります：
* `LLM Provider`を`OpenAI`に設定
* `LLM Model`を使用するモデルに設定
[LiteLLMがサポートするOpenAIモデルの完全なリストはこちらをご覧ください。](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)
モデルがリストにない場合は、`Advanced`オプションを切り替えて、`Custom Model`に入力してください（例：openai/&lt;model-name&gt;、`openai/gpt-4o`など）。
* `API Key`にOpenAI APIキーを設定。OpenAI Project APIキーの確認または作成については、[こちら](https://platform.openai.com/api-keys)をご覧ください。

## OpenAI互換エンドポイントの使用

OpenAIチャット補完と同様に、OpenAI互換エンドポイントにもLiteLLMを使用します。この話題に関する完全なドキュメントは[こちら](https://docs.litellm.ai/docs/providers/openai_compatible)で確認できます。

## OpenAIプロキシの使用

OpenAIプロキシを使用している場合、OpenHandsのUI設定で：
1. `Advanced`オプションを有効にする
2. 以下を設定する：
   - `Custom Model`をopenai/&lt;model-name&gt;に設定（例：`openai/gpt-4o`またはopenai/&lt;proxy-prefix&gt;/&lt;model-name&gt;）
   - `Base URL`をOpenAIプロキシのURLに設定
   - `API Key`をOpenAI APIキーに設定
