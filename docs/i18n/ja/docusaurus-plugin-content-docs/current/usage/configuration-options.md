# 設定オプション

:::note
このページでは、OpenHandsで利用可能なすべての設定オプションを説明しています。これにより、動作をカスタマイズし、他のサービスと統合することができます。GUIモードでは、設定UI経由で適用された設定が優先されます。
:::

## コア設定

コア設定オプションは、`config.toml`ファイルの`[core]`セクションで定義されています。

### APIキー
- `e2b_api_key`
  - 型: `str`
  - デフォルト: `""`
  - 説明: E2BのAPIキー

- `modal_api_token_id`
  - 型: `str`
  - デフォルト: `""`
  - 説明: ModalのAPIトークンID

- `modal_api_token_secret`
  - 型: `str`
  - デフォルト: `""`
  - 説明: ModalのAPIトークンシークレット

### ワークスペース
- `workspace_base` **(非推奨)**
  - 型: `str`
  - デフォルト: `"./workspace"`
  - 説明: ワークスペースのベースパス。**非推奨: 代わりに`SANDBOX_VOLUMES`を使用してください。**

- `cache_dir`
  - 型: `str`
  - デフォルト: `"/tmp/cache"`
  - 説明: キャッシュディレクトリのパス

### デバッグとロギング
- `debug`
  - 型: `bool`
  - デフォルト: `false`
  - 説明: デバッグを有効にする

- `disable_color`
  - 型: `bool`
  - デフォルト: `false`
  - 説明: ターミナル出力の色を無効にする

### トラジェクトリ
- `save_trajectory_path`
  - 型: `str`
  - デフォルト: `"./trajectories"`
  - 説明: トラジェクトリを保存するパス（フォルダまたはファイル）。フォルダの場合、トラジェクトリはセッションID名と.json拡張子を持つファイルにそのフォルダ内に保存されます。

- `replay_trajectory_path`
  - 型: `str`
  - デフォルト: `""`
  - 説明: トラジェクトリをロードして再生するためのパス。指定する場合は、JSON形式のトラジェクトリファイルへのパスである必要があります。トラジェクトリファイル内のアクションは、ユーザー指示が実行される前に最初に再生されます。

### ファイルストア
- `file_store_path`
  - 型: `str`
  - デフォルト: `"/tmp/file_store"`
  - 説明: ファイルストアのパス

- `file_store`
  - 型: `str`
  - デフォルト: `"memory"`
  - 説明: ファイルストアのタイプ

- `file_uploads_allowed_extensions`
  - 型: `list of str`
  - デフォルト: `[".*"]`
  - 説明: アップロード可能なファイル拡張子のリスト

- `file_uploads_max_file_size_mb`
  - 型: `int`
  - デフォルト: `0`
  - 説明: アップロードの最大ファイルサイズ（メガバイト単位）

- `file_uploads_restrict_file_types`
  - 型: `bool`
  - デフォルト: `false`
  - 説明: ファイルアップロードのファイルタイプを制限する

- `file_uploads_allowed_extensions`
  - 型: `list of str`
  - デフォルト: `[".*"]`
  - 説明: アップロード可能なファイル拡張子のリスト

### タスク管理
- `max_budget_per_task`
  - 型: `float`
  - デフォルト: `0.0`
  - 説明: タスクごとの最大予算（0.0は制限なしを意味します）

- `max_iterations`
  - 型: `int`
  - デフォルト: `100`
  - 説明: 最大反復回数

### サンドボックス設定
- `volumes`
  - 型: `str`
  - デフォルト: `None`
  - 説明: 'host_path:container_path[:mode]'形式のボリュームマウント。例：'/my/host/dir:/workspace:rw'。複数のマウントはカンマで区切って指定できます。例：'/path1:/workspace/path1,/path2:/workspace/path2:ro'

- `workspace_mount_path_in_sandbox` **(非推奨)**
  - 型: `str`
  - デフォルト: `"/workspace"`
  - 説明: サンドボックス内にワークスペースをマウントするパス。**非推奨: 代わりに`SANDBOX_VOLUMES`を使用してください。**

- `workspace_mount_path` **(非推奨)**
  - 型: `str`
  - デフォルト: `""`
  - 説明: ワークスペースをマウントするパス。**非推奨: 代わりに`SANDBOX_VOLUMES`を使用してください。**

- `workspace_mount_rewrite` **(非推奨)**
  - 型: `str`
  - デフォルト: `""`
  - 説明: ワークスペースマウントパスを書き換えるパス。通常は無視できます。別のコンテナ内で実行する特殊なケースを指します。**非推奨: 代わりに`SANDBOX_VOLUMES`を使用してください。**

### その他
- `run_as_openhands`
  - 型: `bool`
  - デフォルト: `true`
  - 説明: OpenHandsとして実行する

- `runtime`
  - 型: `str`
  - デフォルト: `"docker"`
  - 説明: ランタイム環境

- `default_agent`
  - 型: `str`
  - デフォルト: `"CodeActAgent"`
  - 説明: デフォルトエージェントの名前

- `jwt_secret`
  - 型: `str`
  - デフォルト: `uuid.uuid4().hex`
  - 説明: 認証用のJWTシークレット。独自の値に設定してください。

## LLM設定

LLM（大規模言語モデル）設定オプションは、`config.toml`ファイルの`[llm]`セクションで定義されています。

これらをdockerコマンドで使用するには、`-e LLM_<option>`を渡します。例：`-e LLM_NUM_RETRIES`。

:::note
開発セットアップでは、カスタム名前付きLLM設定を定義することもできます。詳細は[カスタムLLM設定](./llms/custom-llm-configs)を参照してください。
:::

**AWS認証情報**
- `aws_access_key_id`
  - 型: `str`
  - デフォルト: `""`
  - 説明: AWSアクセスキーID

- `aws_region_name`
  - 型: `str`
  - デフォルト: `""`
  - 説明: AWSリージョン名

- `aws_secret_access_key`
  - 型: `str`
  - デフォルト: `""`
  - 説明: AWSシークレットアクセスキー

### API設定
- `api_key`
  - 型: `str`
  - デフォルト: `None`
  - 説明: 使用するAPIキー

- `base_url`
  - 型: `str`
  - デフォルト: `""`
  - 説明: APIベースURL

- `api_version`
  - 型: `str`
  - デフォルト: `""`
  - 説明: APIバージョン

- `input_cost_per_token`
  - 型: `float`
  - デフォルト: `0.0`
  - 説明: 入力トークンあたりのコスト

- `output_cost_per_token`
  - 型: `float`
  - デフォルト: `0.0`
  - 説明: 出力トークンあたりのコスト

### カスタムLLMプロバイダー
- `custom_llm_provider`
  - 型: `str`
  - デフォルト: `""`
  - 説明: カスタムLLMプロバイダー

### メッセージ処理
- `max_message_chars`
  - 型: `int`
  - デフォルト: `30000`
  - 説明: LLMへのプロンプトに含まれるイベントのコンテンツの最大文字数（概算）。より大きな観測は切り捨てられます。

- `max_input_tokens`
  - 型: `int`
  - デフォルト: `0`
  - 説明: 最大入力トークン数

- `max_output_tokens`
  - 型: `int`
  - デフォルト: `0`
  - 説明: 最大出力トークン数

### モデル選択
- `model`
  - 型: `str`
  - デフォルト: `"claude-3-5-sonnet-20241022"`
  - 説明: 使用するモデル

### リトライ
- `num_retries`
  - 型: `int`
  - デフォルト: `8`
  - 説明: 試行するリトライ回数

- `retry_max_wait`
  - 型: `int`
  - デフォルト: `120`
  - 説明: リトライ試行間の最大待機時間（秒）

- `retry_min_wait`
  - 型: `int`
  - デフォルト: `15`
  - 説明: リトライ試行間の最小待機時間（秒）

- `retry_multiplier`
  - 型: `float`
  - デフォルト: `2.0`
  - 説明: 指数バックオフ計算の乗数

### 高度なオプション
- `drop_params`
  - 型: `bool`
  - デフォルト: `false`
  - 説明: マッピングされていない（サポートされていない）パラメータを例外を発生させずに削除する

- `caching_prompt`
  - 型: `bool`
  - デフォルト: `true`
  - 説明: LLMによって提供され、サポートされている場合、プロンプトキャッシュ機能を使用する

- `ollama_base_url`
  - 型: `str`
  - デフォルト: `""`
  - 説明: OLLAMA APIのベースURL

- `temperature`
  - 型: `float`
  - デフォルト: `0.0`
  - 説明: APIの温度

- `timeout`
  - 型: `int`
  - デフォルト: `0`
  - 説明: APIのタイムアウト

- `top_p`
  - 型: `float`
  - デフォルト: `1.0`
  - 説明: APIのtop p

- `disable_vision`
  - 型: `bool`
  - デフォルト: `None`
  - 説明: モデルがビジョン対応の場合、このオプションで画像処理を無効にできます（コスト削減に役立ちます）

## エージェント設定

エージェント設定オプションは、`config.toml`ファイルの`[agent]`および`[agent.<agent_name>]`セクションで定義されています。

### LLM設定
- `llm_config`
  - 型: `str`
  - デフォルト: `'your-llm-config-group'`
  - 説明: 使用するLLM設定の名前

### ActionSpace設定
- `function_calling`
  - 型: `bool`
  - デフォルト: `true`
  - 説明: 関数呼び出しが有効かどうか

- `enable_browsing`
  - 型: `bool`
  - デフォルト: `false`
  - 説明: アクションスペースでブラウジングデリゲートが有効かどうか（関数呼び出しでのみ機能します）

- `enable_llm_editor`
  - 型: `bool`
  - デフォルト: `false`
  - 説明: アクションスペースでLLMエディタが有効かどうか（関数呼び出しでのみ機能します）

- `enable_jupyter`
  - 型: `bool`
  - デフォルト: `false`
  - 説明: アクションスペースでJupyterが有効かどうか

- `enable_history_truncation`
  - 型: `bool`
  - デフォルト: `true`
  - 説明: LLMコンテキスト長の制限に達したときにセッションを続行するために履歴を切り詰めるかどうか

### マイクロエージェントの使用
- `enable_prompt_extensions`
  - 型: `bool`
  - デフォルト: `true`
  - 説明: マイクロエージェントを使用するかどうか

- `disabled_microagents`
  - 型: `list of str`
  - デフォルト: `None`
  - 説明: 無効にするマイクロエージェントのリスト

## サンドボックス設定

サンドボックス設定オプションは、`config.toml`ファイルの`[sandbox]`セクションで定義されています。

これらをdockerコマンドで使用するには、`-e SANDBOX_<option>`を渡します。例：`-e SANDBOX_TIMEOUT`。

### 実行
- `timeout`
  - 型: `int`
  - デフォルト: `120`
  - 説明: サンドボックスのタイムアウト（秒）

- `user_id`
  - 型: `int`
  - デフォルト: `1000`
