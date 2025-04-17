# 設定オプション

このガイドでは、OpenHandsで利用可能なすべての設定オプションを詳しく説明し、その動作をカスタマイズし、他のサービスと統合するのに役立ちます。

:::note
[GUIモード](https://docs.all-hands.dev/modules/usage/how-to/gui-mode)で実行している場合、設定UIで利用可能な設定が常に優先されます。
:::

---

# 目次

1. [基本設定](#core-configuration)
   - [APIキー](#api-keys)
   - [ワークスペース](#workspace)
   - [デバッグとロギング](#debugging-and-logging)
   - [トラジェクトリ](#trajectories)
   - [ファイルストア](#file-store)
   - [タスク管理](#task-management)
   - [サンドボックス設定](#sandbox-configuration)
   - [その他](#miscellaneous)
2. [LLM設定](#llm-configuration)
   - [AWS認証情報](#aws-credentials)
   - [API設定](#api-configuration)
   - [カスタムLLMプロバイダー](#custom-llm-provider)
   - [埋め込み](#embeddings)
   - [メッセージ処理](#message-handling)
   - [モデル選択](#model-selection)
   - [リトライ](#retrying)
   - [詳細オプション](#advanced-options)
3. [エージェント設定](#agent-configuration)
   - [メモリ設定](#memory-configuration)
   - [LLM設定](#llm-configuration-1)
   - [アクションスペース設定](#actionspace-configuration)
   - [マイクロエージェントの使用](#microagent-usage)
4. [サンドボックス設定](#sandbox-configuration-1)
   - [実行](#execution)
   - [コンテナイメージ](#container-image)
   - [ネットワーキング](#networking)
   - [リンティングとプラグイン](#linting-and-plugins)
   - [依存関係と環境](#dependencies-and-environment)
   - [評価](#evaluation)
5. [セキュリティ設定](#security-configuration)
   - [確認モード](#confirmation-mode)
   - [セキュリティアナライザー](#security-analyzer)

---

## 基本設定

基本設定オプションは`config.toml`ファイルの`[core]`セクションで定義されます。

**APIキー**
- `e2b_api_key`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: E2BのAPIキー

- `modal_api_token_id`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: ModalのAPIトークンID

- `modal_api_token_secret`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: ModalのAPIトークンシークレット

**ワークスペース**
- `workspace_base`
  - 型: `str`
  - デフォルト値: `"./workspace"`
  - 説明: ワークスペースのベースパス

- `cache_dir`
  - 型: `str`
  - デフォルト値: `"/tmp/cache"`
  - 説明: キャッシュディレクトリのパス

**デバッグとロギング**
- `debug`
  - 型: `bool`
  - デフォルト値: `false`
  - 説明: デバッグを有効にする

- `disable_color`
  - 型: `bool`
  - デフォルト値: `false`
  - 説明: ターミナル出力のカラー表示を無効にする

**トラジェクトリ**
- `save_trajectory_path`
  - 型: `str`
  - デフォルト値: `"./trajectories"`
  - 説明: トラジェクトリを保存するパス（フォルダまたはファイル）。フォルダの場合、トラジェクトリはセッションIDと.json拡張子を持つファイルとしてそのフォルダに保存されます。

**ファイルストア**
- `file_store_path`
  - 型: `str`
  - デフォルト値: `"/tmp/file_store"`
  - 説明: ファイルストアのパス

- `file_store`
  - 型: `str`
  - デフォルト値: `"memory"`
  - 説明: ファイルストアのタイプ

- `file_uploads_allowed_extensions`
  - 型: `list of str`
  - デフォルト値: `[".*"]`
  - 説明: アップロードを許可するファイル拡張子のリスト

- `file_uploads_max_file_size_mb`
  - 型: `int`
  - デフォルト値: `0`
  - 説明: アップロードの最大ファイルサイズ（メガバイト）

- `file_uploads_restrict_file_types`
  - 型: `bool`
  - デフォルト値: `false`
  - 説明: ファイルアップロードのファイルタイプを制限する

**タスク管理**
- `max_budget_per_task`
  - 型: `float`
  - デフォルト値: `0.0`
  - 説明: タスクごとの最大予算（0.0は制限なし）

- `max_iterations`
  - 型: `int`
  - デフォルト値: `100`
  - 説明: 最大イテレーション数

**サンドボックス設定**
- `workspace_mount_path_in_sandbox`
  - 型: `str`
  - デフォルト値: `"/workspace"`
  - 説明: サンドボックス内のワークスペースマウントパス

- `workspace_mount_path`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: ワークスペースマウントパス

- `workspace_mount_rewrite`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: ワークスペースマウントパスを書き換えるパス。通常は無視できます。別のコンテナ内での実行の特殊なケースを参照します。

**その他**
- `run_as_openhands`
  - 型: `bool`
  - デフォルト値: `true`
  - 説明: OpenHandsとして実行する

- `runtime`
  - 型: `str`
  - デフォルト値: `"docker"`
  - 説明: 実行環境

- `default_agent`
  - 型: `str`
  - デフォルト値: `"CodeActAgent"`
  - 説明: デフォルトのエージェント名

- `jwt_secret`
  - 型: `str`
  - デフォルト値: `uuid.uuid4().hex`
  - 説明: 認証用のJWTシークレット。独自の値に設定してください。

## LLM設定

LLM（大規模言語モデル）設定オプションは`config.toml`ファイルの`[llm]`セクションで定義されます。

dockerコマンドで使用する場合は、`-e LLM_<option>`として渡します。例：`-e LLM_NUM_RETRIES`

:::note
開発設定では、カスタムLLM設定も定義できます。詳細は[カスタムLLM設定](./llms/custom-llm-configs)を参照してください。
:::

**AWS認証情報**
- `aws_access_key_id`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: AWSアクセスキーID

- `aws_region_name`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: AWSリージョン名

- `aws_secret_access_key`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: AWSシークレットアクセスキー

**API設定**
- `api_key`
  - 型: `str`
  - デフォルト値: `None`
  - 説明: 使用するAPIキー

- `base_url`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: APIのベースURL

- `api_version`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: APIバージョン

- `input_cost_per_token`
  - 型: `float`
  - デフォルト値: `0.0`
  - 説明: 入力トークンあたりのコスト

- `output_cost_per_token`
  - 型: `float`
  - デフォルト値: `0.0`
  - 説明: 出力トークンあたりのコスト

**カスタムLLMプロバイダー**
- `custom_llm_provider`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: カスタムLLMプロバイダー

**埋め込み**
- `embedding_base_url`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: 埋め込みAPIのベースURL

- `embedding_deployment_name`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: 埋め込みデプロイメント名

- `embedding_model`
  - 型: `str`
  - デフォルト値: `"local"`
  - 説明: 使用する埋め込みモデル

**メッセージ処理**
- `max_message_chars`
  - 型: `int`
  - デフォルト値: `30000`
  - 説明: LLMプロンプトに含まれるイベントコンテンツの最大文字数（概算）。より大きな観察は切り捨てられます。

- `max_input_tokens`
  - 型: `int`
  - デフォルト値: `0`
  - 説明: 最大入力トークン数

- `max_output_tokens`
  - 型: `int`
  - デフォルト値: `0`
  - 説明: 最大出力トークン数

**モデル選択**
- `model`
  - 型: `str`
  - デフォルト値: `"claude-3-5-sonnet-20241022"`
  - 説明: 使用するモデル

**リトライ**
- `num_retries`
  - 型: `int`
  - デフォルト値: `8`
  - 説明: リトライ回数

- `retry_max_wait`
  - 型: `int`
  - デフォルト値: `120`
  - 説明: リトライ間の最大待機時間（秒）

- `retry_min_wait`
  - 型: `int`
  - デフォルト値: `15`
  - 説明: リトライ間の最小待機時間（秒）

- `retry_multiplier`
  - 型: `float`
  - デフォルト値: `2.0`
  - 説明: 指数バックオフ計算の乗数

**詳細オプション**
- `drop_params`
  - 型: `bool`
  - デフォルト値: `false`
  - 説明: マッピングされていない（サポートされていない）パラメータを例外を発生させずに削除する

- `caching_prompt`
  - 型: `bool`
  - デフォルト値: `true`
  - 説明: LLMによって提供され、サポートされている場合、プロンプトキャッシュ機能を使用する

- `ollama_base_url`
  - 型: `str`
  - デフォルト値: `""`
  - 説明: OLLAMA APIのベースURL

- `temperature`
  - 型: `float`
  - デフォルト値: `0.0`
  - 説明: APIの温度パラメータ

- `timeout`
  - 型: `int`
  - デフォルト値: `0`
  - 説明: APIのタイムアウト

- `top_p`
  - 型: `float`
  - デフォルト値: `1.0`
  - 説明: APIのtop_pパラメータ

- `disable_vision`
  - 型: `bool`
  - デフォルト値: `None`
  - 説明: モデルがビジョン機能を持つ場合、この設定で画像処理を無効にできます（コスト削減に有用）

## エージェント設定

エージェント設定オプションは`config.toml`ファイルの`[agent]`および`[agent.<agent_name>]`セクションで定義されます。

**メモリ設定**
- `memory_enabled`
  - 型: `bool`
  - デフォルト値: `false`
  - 説明: 長期メモリ（埋め込み）が有効かどうか

- `memory_max_threads`
  - 型: `int`
  - デフォルト値: `3`
  - 説明: 埋め込みのために同時にインデックスを作成する最大スレッド数

**LLM設定**
- `llm_config`
  - 型: `str`
  - デフォルト値: `'your-llm-config-group'`
  - 説明: 使用するLLM設定の名前

**アクションスペース設定**
- `function_calling`
  - 型: `bool`
  - デフォルト値: `true`
  - 説明: 関数呼び出しが有効かどうか

- `enable_browsing`
  - 型: `bool`
  - デフォルト値: `false`
  - 説明: アクションスペースでブラウジングデリゲートが有効かどうか（関数呼び出しでのみ機能）

- `enable_llm_editor`
  - 型: `bool`
  - デフォルト値: `false`
  - 説明: アクションスペースでLLMエディタが有効かどうか（関数呼び出しでのみ機能）

**マイクロエージェントの使用**
- `enable_prompt_extensions`
  - 型: `bool`
  - デフォルト値: `true`
  - 説明: マイクロエージェントの使用が有効かどうか

- `disabled_microagents`
  - 型: `list of str`
  - デフォルト値: `None`
  - 説明: 無効にするマイクロエージェントのリスト

### 実行
- `timeout`
  - 型: `int`
  - デフォルト値: `120`
  - 説明: サンドボックスのタイムアウト（秒）

- `user_id`
  - 型: `int`
  - デフォルト値: `1000`
  - 説明: サンドボックスのユーザーID
