# LiteLLM プロキシ

OpenHandsは、様々なLLMプロバイダーにアクセスするために[LiteLLMプロキシ](https://docs.litellm.ai/docs/proxy/quick_start)の使用をサポートしています。

## 設定

OpenHandsでLiteLLMプロキシを使用するには、以下の手順が必要です：

1. LiteLLMプロキシサーバーを設定する（[LiteLLMのドキュメント](https://docs.litellm.ai/docs/proxy/quick_start)を参照）
2. OpenHandsを実行する際、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：
  * `詳細設定`を有効にする
  * `カスタムモデル`にプレフィックス`litellm_proxy/`と使用するモデルを設定（例：`litellm_proxy/anthropic.claude-3-5-sonnet-20241022-v2:0`）
  * `ベースURL`をLiteLLMプロキシのURL（例：`https://your-litellm-proxy.com`）に設定
  * `APIキー`をLiteLLMプロキシのAPIキーに設定

## サポートされているモデル

サポートされているモデルは、LiteLLMプロキシの設定に依存します。OpenHandsは、LiteLLMプロキシが処理するように設定されているすべてのモデルをサポートします。

利用可能なモデルとその名前のリストについては、LiteLLMプロキシの設定を参照してください。
