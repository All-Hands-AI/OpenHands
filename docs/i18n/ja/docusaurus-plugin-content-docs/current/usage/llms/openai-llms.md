# OpenAI

OpenHandsは、OpenAIのチャットモデルへのAPIコールにLiteLLMを使用します。OpenAIをプロバイダーとして使用する方法については、[こちら](https://docs.litellm.ai/docs/providers/openai)のドキュメントを参照してください。

## 設定

OpenHandsを実行する際、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：
* `LLM Provider`を`OpenAI`に設定
* `LLM Model`を使用するモデルに設定。
[LiteLLMがサポートするOpenAIモデルの完全なリストはこちら](https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models)を参照してください。
モデルがリストにない場合は、`Advanced Options`を有効にし、`Custom Model`に入力してください（例：openai/&lt;model-name&gt;として`openai/gpt-4o`）。
* `API Key`をOpenAI APIキーに設定。OpenAIプロジェクトのAPIキーの確認または作成については、[こちら](https://platform.openai.com/api-keys)を参照してください。

## OpenAI互換エンドポイントの使用

OpenAIのチャット補完と同様に、OpenAI互換エンドポイントにもLiteLLMを使用します。この件に関する完全なドキュメントは[こちら](https://docs.litellm.ai/docs/providers/openai_compatible)を参照してください。

## OpenAIプロキシの使用

OpenAIプロキシを使用する場合、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：
* `Advanced Options`を有効にする
* `Custom Model`をopenai/&lt;model-name&gt;に設定（例：`openai/gpt-4o`またはopenai/&lt;proxy-prefix&gt;/&lt;model-name&gt;）
* `Base URL`をOpenAIプロキシのURLに設定
* `API Key`をOpenAI APIキーに設定
