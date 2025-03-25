# カスタムLLM設定

OpenHandsでは、`config.toml`ファイルで複数の名前付きLLM設定を定義できます。この機能により、高品質な応答が不要なタスクには低コストのモデルを使用したり、特定のエージェントに対して異なるパラメータを持つ異なるモデルを使用したりするなど、異なる用途に応じて異なるLLM設定を使用できます。

## 仕組み

名前付きLLM設定は、`config.toml`ファイルで`llm.`で始まるセクションを使用して定義されます。例：

```toml
# デフォルトのLLM設定
[llm]
model = "gpt-4"
api_key = "あなたのAPIキー"
temperature = 0.0

# 低コストモデル用のカスタムLLM設定
[llm.gpt3]
model = "gpt-3.5-turbo"
api_key = "あなたのAPIキー"
temperature = 0.2

# 異なるパラメータを持つ別のカスタム設定
[llm.high-creativity]
model = "gpt-4"
api_key = "あなたのAPIキー"
temperature = 0.8
top_p = 0.9
```

各名前付き設定は、デフォルトの`[llm]`セクションからすべてのパラメータを継承し、これらのパラメータを上書きできます。必要な数のカスタム設定を定義できます。

## カスタム設定の使用

### エージェントでの使用

エージェントの設定セクションで`llm_config`パラメータを設定することで、エージェントが使用するLLM設定を指定できます：

```toml
[agent.RepoExplorerAgent]
# このエージェントには低コストのGPT-3設定を使用
llm_config = 'gpt3'

[agent.CodeWriterAgent]
# このエージェントには高創造性の設定を使用
llm_config = 'high-creativity'
```

### 設定オプション

各名前付きLLM設定は、デフォルトのLLM設定と同じすべてのオプションをサポートしています。これらには以下が含まれます：

- モデルの選択（`model`）
- API設定（`api_key`、`base_url`など）
- モデルパラメータ（`temperature`、`top_p`など）
- リトライパラメータ（`num_retries`、`retry_multiplier`など）
- トークン制限（`max_input_tokens`、`max_output_tokens`）
- その他すべてのLLM設定オプション

利用可能なオプションの完全なリストについては、[設定オプション](../configuration-options)のドキュメントのLLM設定セクションを参照してください。

## ユースケース

カスタムLLM設定は、以下のようなシナリオで特に有用です：

- **コスト最適化**：リポジトリの探索やシンプルなファイル操作など、高品質な応答が不要なタスクには低コストのモデルを使用
- **タスク固有の調整**：異なるレベルの創造性や決定論的な応答が必要なタスクに対して、異なるtemperatureやtop_p値を設定
- **異なるプロバイダー**：異なるタスクに対して異なるLLMプロバイダーやAPIエンドポイントを使用
- **テストと開発**：開発とテスト中に異なるモデル設定を簡単に切り替え

## 例：コスト最適化

コスト最適化のためのカスタムLLM設定の実践的な例：

```toml
# 高品質な応答用のGPT-4を使用するデフォルト設定
[llm]
model = "gpt-4"
api_key = "あなたのAPIキー"
temperature = 0.0

# リポジトリ探索用の低コスト設定
[llm.repo-explorer]
model = "gpt-3.5-turbo"
temperature = 0.2

# コード生成用の設定
[llm.code-gen]
model = "gpt-4"
temperature = 0.0
max_output_tokens = 2000

[agent.RepoExplorerAgent]
llm_config = 'repo-explorer'

[agent.CodeWriterAgent]
llm_config = 'code-gen'
```

この例では：
- リポジトリ探索は主にコードの理解とナビゲーションなので、低コストモデルを使用
- コード生成は、より大きなコードブロックを生成するためにGPT-4とより高いトークン制限を使用
- デフォルト設定は他のタスクで引き続き利用可能

:::note
カスタムLLM設定は、`main.py`または`cli.py`を介して開発モードでOpenHandsを使用する場合にのみ利用可能です。`docker run`を介して実行する場合は、標準の設定オプションを使用してください。
:::
