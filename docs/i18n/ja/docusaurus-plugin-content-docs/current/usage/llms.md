# 🤖 LLMバックエンド

OpenHandsは、LiteLLMがサポートするすべてのLLMに接続できます。ただし、機能するには強力なモデルが必要です。

## モデルの推奨事項

コーディングタスクに対する言語モデルの評価（SWE-benchデータセットを使用）に基づいて、モデル選択に関するいくつかの推奨事項を提供できます。分析の一部は、[LLMを比較したこのブログ記事](https://www.all-hands.dev/blog/evaluation-of-llms-as-coding-agents-on-swe-bench-at-30x-speed)と[より最近の結果を含むこのブログ記事](https://www.all-hands.dev/blog/openhands-codeact-21-an-open-state-of-the-art-software-development-agent)で確認できます。

モデルを選択する際は、出力の品質とコストの両方を考慮してください。結果の要約は以下の通りです：

* Claude 3.5 Sonnetが圧倒的に優れており、OpenHandsのデフォルトエージェントでSWE-Bench Verifiedの53%の解決率を達成しています。
* GPT-4oは遅れを取っており、o1-miniは実際にGPT-4oよりもわずかに低いパフォーマンスを示しました。結果を少し分析したところ、o1は時々「考えすぎ」て、タスクを完了できるのに追加の環境設定タスクを実行していたようです。
* 最後に、最も強力なオープンモデルはLlama 3.1 405 BとDeepseek-v2.5で、合理的なパフォーマンスを示し、一部のクローズドモデルを上回りました。

詳細については、[完全な記事](https://www.all-hands.dev/blog/evaluation-of-llms-as-coding-agents-on-swe-bench-at-30x-speed)を参照してください。

これらの結果とコミュニティからのフィードバックに基づいて、以下のモデルがOpenHandsで合理的に機能することが確認されています：

* claude-3-5-sonnet（推奨）
* gpt-4 / gpt-4o
* llama-3.1-405b
* deepseek-v2.5

:::warning prudence
OpenHandsは、設定したLLMに多くのプロンプトを送信します。これらのLLMのほとんどは有料なので、支出制限を設定し、使用状況を監視してください。
:::

リストにない特定のLLMでOpenHandsの実行に成功した場合は、検証済みリストに追加してください。また、同じプロバイダーとLLMを使用する他のユーザーを支援するため、設定プロセスを共有するPRを開くことをお勧めします！

利用可能なプロバイダーとモデルの完全なリストについては、[litellmのドキュメント](https://docs.litellm.ai/docs/providers)を参照してください。

:::note remarque
現在のほとんどのローカルおよびオープンソースモデルは、それほど強力ではありません。このようなモデルを使用する場合、メッセージ間の長い待機時間、品質の低い応答、または不正なJSONに関するエラーが発生する可能性があります。OpenHandsは、それを駆動するモデルと同じくらい強力にしかなりません。ただし、機能するモデルを見つけた場合は、上記の検証済みリストに追加してください。
:::

## LLM設定

以下の項目は、OpenHandsのUIで設定メニューから設定できます：

* `LLMプロバイダー`
* `LLMモデル`
* `APIキー`
* `ベースURL`（`詳細設定`から）

一部のLLM/プロバイダーで必要となる可能性があるが、UIでは設定できないパラメータがあります。これらは代わりに、[docker runコマンド](./installation#start-the-app)に`-e`を使用して環境変数として渡すことができます：

* `LLM_API_VERSION`
* `LLM_EMBEDDING_MODEL`
* `LLM_EMBEDDING_DEPLOYMENT_NAME`
* `LLM_DROP_PARAMS`
* `LLM_DISABLE_VISION`
* `LLM_CACHING_PROMPT`

特定のモデルプロバイダーでOpenHandsを実行するためのガイドがいくつかあります：

* [Azure](./llms/azure-llms)
* [Google](./llms/google-llms)
* [Groq](./llms/groq)
* [LiteLLM Proxy](./llms/litellm-proxy)
* [OpenAI](./llms/openai-llms)
* [OpenRouter](./llms/openrouter)

### APIリトライとレート制限

LLMプロバイダーは通常、レート制限を持っており、時には非常に低い制限で、リトライが必要になる場合があります。OpenHandsは、レート制限エラー（エラーコード429）、API接続エラー、またはその他の一時的なエラーを受信した場合、自動的にリクエストを再試行します。

使用しているプロバイダーのニーズに応じて、これらのオプションをカスタマイズできます。プロバイダーのドキュメントを確認し、以下の環境変数を設定してリトライ回数とリトライ間の待機時間を制御してください：

* `LLM_NUM_RETRIES`（デフォルト8）
* `LLM_RETRY_MIN_WAIT`（デフォルト15秒）
* `LLM_RETRY_MAX_WAIT`（デフォルト120秒）
* `LLM_RETRY_MULTIPLIER`（デフォルト2）

OpenHandsを開発モードで実行している場合、これらのオプションを`config.toml`ファイルで設定することもできます：

```toml
[llm]
num_retries = 8
retry_min_wait = 15
retry_max_wait = 120
retry_multiplier = 2
```
