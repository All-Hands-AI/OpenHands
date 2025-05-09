# LiteLLM プロキシ

OpenHandsは[LiteLLMプロキシ](https://docs.litellm.ai/docs/proxy/quick_start)を使用して、様々なLLMプロバイダーにアクセスすることをサポートしています。

## 設定

OpenHandsでLiteLLMプロキシを使用するには、以下の手順が必要です：

1. LiteLLMプロキシサーバーをセットアップする（[LiteLLMドキュメント](https://docs.litellm.ai/docs/proxy/quick_start)を参照）
2. OpenHandsを実行する際、設定画面から以下の項目を設定する必要があります：
  * `Advanced`（詳細設定）オプションを有効にする
  * `Custom Model`（カスタムモデル）に接頭辞 `litellm_proxy/` + 使用するモデル名を設定する（例：`litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0`）
  * `Base URL`（ベースURL）にLiteLLMプロキシのURLを設定する（例：`https://your-litellm-proxy.com`）
  * `API Key`（APIキー）にLiteLLMプロキシのAPIキーを設定する

## サポートされているモデル

サポートされているモデルはLiteLLMプロキシの設定によって異なります。OpenHandsはLiteLLMプロキシが対応するように設定されているあらゆるモデルをサポートします。

利用可能なモデルとその名前のリストについては、LiteLLMプロキシの設定を参照してください。
