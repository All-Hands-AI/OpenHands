# カスタムLLM設定

OpenHandsでは、`config.toml`ファイルに複数の名前付きLLM設定を定義することができます。この機能により、異なる目的に応じて異なるLLM設定を使用することができます。例えば、高品質な応答を必要としないタスクには安価なモデルを使用したり、特定のエージェントに対して異なるパラメータを持つ異なるモデルを使用したりすることができます。

## 仕組み

名前付きLLM設定は、`config.toml`ファイルで`llm.`で始まるセクションを使用して定義されます。例えば：

```toml
# デフォルトLLM設定
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# 安価なモデル用のカスタムLLM設定
[llm.gpt3]
model = "gpt-3.5-turbo"
api_key = "your-api-key"
temperature = 0.2

# 異なるパラメータを持つ別のカスタム設定
[llm.high-creativity]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.8
top_p = 0.9
```

各名前付き設定は、デフォルトの`[llm]`セクションからすべての設定を継承し、それらの設定を上書きすることができます。必要な数だけカスタム設定を定義できます。

## カスタム設定の使用方法

### エージェントでの使用

エージェントの設定セクションで`llm_config`パラメータを設定することで、エージェントが使用するLLM設定を指定できます：

```toml
[agent.RepoExplorerAgent]
# このエージェントには安価なGPT-3設定を使用
llm_config = 'gpt3'

[agent.CodeWriterAgent]
# このエージェントには高創造性設定を使用
llm_config = 'high-creativity'
```

### 設定オプション

各名前付きLLM設定は、デフォルトのLLM設定と同じオプションをすべてサポートしています。これらには以下が含まれます：

- モデル選択（`model`）
- API設定（`api_key`、`base_url`など）
- モデルパラメータ（`temperature`、`top_p`など）
- リトライ設定（`num_retries`、`retry_multiplier`など）
- トークン制限（`max_input_tokens`、`max_output_tokens`）
- その他すべてのLLM設定オプション

利用可能なオプションの完全なリストについては、[設定オプション](../configuration-options)ドキュメントのLLM設定セクションを参照してください。

## ユースケース

カスタムLLM設定は、特に以下のシナリオで役立ちます：

- **コスト最適化**：リポジトリの探索や単純なファイル操作など、高品質な応答を必要としないタスクには安価なモデルを使用します。
- **タスク固有の調整**：異なるレベルの創造性や決定論を必要とするタスクに対して、異なる温度やtop_p値を設定します。
- **異なるプロバイダー**：異なるタスクに対して異なるLLMプロバイダーやAPIエンドポイントを使用します。
- **テストと開発**：開発とテスト中に異なるモデル設定を簡単に切り替えることができます。

## 例：コスト最適化

カスタムLLM設定を使用してコストを最適化する実用的な例：

```toml
# 高品質な応答のためのGPT-4を使用するデフォルト設定
[llm]
model = "gpt-4"
api_key = "your-api-key"
temperature = 0.0

# リポジトリ探索用の安価な設定
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
- リポジトリ探索は主にコードの理解とナビゲーションを含むため、安価なモデルを使用します
- コード生成は、より大きなコードブロックを生成するためにGPT-4とより高いトークン制限を使用します
- デフォルト設定は他のタスクで引き続き利用可能です

# 予約名を持つカスタム設定

OpenHandsは、特定のユースケースのために予約名を持つカスタムLLM設定を使用することができます。予約名の下でモデルやその他の設定を指定すると、OpenHandsはそれらを特定の目的のために読み込んで使用します。現在、そのような設定の一つが実装されています：ドラフトエディター。

## ドラフトエディター設定

`draft_editor`設定は、コードの編集や改良を含むタスクのために、コード編集の予備的な草案作成に使用するモデルを指定するための設定グループです。これを`[llm.draft_editor]`セクションの下に提供する必要があります。

例えば、`config.toml`で次のようなドラフトエディターを定義できます：

```toml
[llm.draft_editor]
model = "gpt-4"
temperature = 0.2
top_p = 0.95
presence_penalty = 0.0
frequency_penalty = 0.0
```

この設定：
- 高品質な編集と提案のためにGPT-4を使用します
- 一貫性を維持しながらも柔軟性を許容するために低い温度（0.2）を設定します
- 幅広いトークンオプションを考慮するために高いtop_p値（0.95）を使用します
- 必要な特定の編集に焦点を当てるためにpresenceとfrequencyのペナルティを無効にします

この設定は、編集を行う前にLLMに編集の草案を作成させたい場合に使用します。一般的に、以下の場合に役立ちます：
- コードの改善を確認して提案する
- コアの意味を維持しながら既存のコンテンツを改良する
- コードやテキストに正確で焦点を絞った変更を加える

:::note
カスタムLLM設定は、`main.py`または`cli.py`を介して開発モードでOpenHandsを使用する場合にのみ利用可能です。`docker run`を介して実行する場合は、標準の設定オプションを使用してください。
:::
