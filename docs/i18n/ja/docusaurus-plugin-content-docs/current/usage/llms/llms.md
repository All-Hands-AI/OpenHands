# 🤖 LLMバックエンド

:::note
このセクションは、OpenHandsを異なるLLMに接続したいユーザー向けです。
:::

OpenHandsはLiteLLMでサポートされているあらゆるLLMに接続できます。ただし、動作するには強力なモデルが必要です。

## モデルの推奨

コーディングタスク向けの言語モデル評価（SWE-benchデータセットを使用）に基づいて、モデル選択についていくつかの
推奨事項を提供できます。最新のベンチマーク結果は[このスプレッドシート](https://docs.google.com/spreadsheets/d/1wOUdFCMyY6Nt0AIqF705KN4JKOWgeI4wUGUP60krXXs/edit?gid=0)で確認できます。

これらの調査結果とコミュニティからのフィードバックに基づき、以下のモデルはOpenHandsでうまく動作することが確認されています：

- [anthropic/claude-3-7-sonnet-20250219](https://www.anthropic.com/api) (推奨)
- [gemini/gemini-2.5-pro](https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/)
- [deepseek/deepseek-chat](https://api-docs.deepseek.com/)
- [openai/o3-mini](https://openai.com/index/openai-o3-mini/)
- [openai/o3](https://openai.com/index/introducing-o3-and-o4-mini/)
- [openai/o4-mini](https://openai.com/index/introducing-o3-and-o4-mini/)
- [all-hands/openhands-lm-32b-v0.1](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model) -- [OpenRouter](https://openrouter.ai/all-hands/openhands-lm-32b-v0.1)を通じて利用可能


:::warning
OpenHandsは設定したLLMに多くのプロンプトを送信します。これらのLLMのほとんどは有料なので、支出制限を設定し、
使用状況を監視してください。
:::

リストにないLLMでOpenHandsを正常に実行できた場合は、検証済みリストに追加してください。
また、同じプロバイダーとLLMを使用している他のユーザーを支援するために、セットアッププロセスを共有するPRを開くことをお勧めします！

利用可能なプロバイダーとモデルの完全なリストについては、
[litellmのドキュメント](https://docs.litellm.ai/docs/providers)を参照してください。

:::note
現在のほとんどのローカルおよびオープンソースモデルはそれほど強力ではありません。そのようなモデルを使用すると、
メッセージ間の長い待ち時間、質の低い応答、または不正なJSON形式に関するエラーが発生する可能性があります。OpenHandsは
それを駆動するモデルと同じくらい強力にしかなりません。ただし、うまく動作するモデルを見つけた場合は、上記の検証済みリストに追加してください。
:::

## LLM設定

以下の設定は、OpenHandsのUI内の設定から行うことができます：

- `LLMプロバイダー`
- `LLMモデル`
- `APIキー`
- `ベースURL`（`詳細設定`から）

一部のLLM/プロバイダーでは、UI経由で設定できない設定が必要な場合があります。これらは
アプリを起動する際にdocker runコマンドに`-e`を使って環境変数として渡すことができます：

- `LLM_API_VERSION`
- `LLM_EMBEDDING_MODEL`
- `LLM_EMBEDDING_DEPLOYMENT_NAME`
- `LLM_DROP_PARAMS`
- `LLM_DISABLE_VISION`
- `LLM_CACHING_PROMPT`

特定のモデルプロバイダーでOpenHandsを実行するためのガイドがいくつかあります：

- [Azure](llms/azure-llms)
- [Google](llms/google-llms)
- [Groq](llms/groq)
- [SGLangまたはvLLMを使用したローカルLLM](llms/../local-llms.md)
- [LiteLLM Proxy](llms/litellm-proxy)
- [OpenAI](llms/openai-llms)
- [OpenRouter](llms/openrouter)

### APIリトライとレート制限

LLMプロバイダーには通常レート制限があり、場合によっては非常に低く設定されていて、リトライが必要になることがあります。OpenHandsは
レート制限エラー（429エラーコード）を受け取った場合、自動的にリクエストを再試行します。

使用しているプロバイダーに合わせてこれらのオプションをカスタマイズできます。プロバイダーのドキュメントを確認し、
リトライ回数とリトライ間の時間を制御するために以下の環境変数を設定してください：

- `LLM_NUM_RETRIES`（デフォルトは4回）
- `LLM_RETRY_MIN_WAIT`（デフォルトは5秒）
- `LLM_RETRY_MAX_WAIT`（デフォルトは30秒）
- `LLM_RETRY_MULTIPLIER`（デフォルトは2）

開発モードでOpenHandsを実行している場合は、`config.toml`ファイルでこれらのオプションを設定することもできます：

```toml
[llm]
num_retries = 4
retry_min_wait = 5
retry_max_wait = 30
retry_multiplier = 2
```
