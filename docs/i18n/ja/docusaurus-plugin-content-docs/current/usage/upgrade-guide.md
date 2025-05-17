# ⬆️ アップグレードガイド

## 0.8.0 (2024-07-13)

### 重要な設定変更

このバージョンでは、バックエンドの設定にいくつかの重要な変更を導入しました。
OpenHandsをフロントエンドインターフェース（Webインターフェース）のみで使用していた場合、特に対応は必要ありません。

以下は、設定の重要な変更点のリストです。これらは`main.py`経由でOpenHands CLIを使用しているユーザーにのみ適用されます。
詳細については、[#2756](https://github.com/All-Hands-AI/OpenHands/pull/2756)を参照してください。

#### main.pyの--model-nameオプションの削除

`--model-name`オプション（または`-m`）は廃止されました。LLMの設定は`config.toml`または環境変数で行う必要があります。

#### LLM設定グループは'llm'のサブグループである必要がある

0.8より前のバージョンでは、`config.toml`内のLLM設定に任意の名前を使用できました。例:

```toml
[gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

その後、CLI引数の`--llm-config`を使用して、名前で目的のLLM設定グループを指定できました。
これは機能しなくなりました。代わりに、設定グループは`llm`グループの下にある必要があります。例:

```toml
[llm.gpt-4o]
model="gpt-4o"
api_key="<your_api_key>"
```

`llm`という名前の設定グループがある場合は、変更する必要はありません。デフォルトのLLM設定グループとして使用されます。

#### 'agent'グループには'name'フィールドが含まれなくなった

0.8より前のバージョンでは、以下のような`agent`という名前の設定グループがあってもなくてもよかったです:

```toml
[agent]
name="CodeActAgent"
memory_max_threads=2
```

`name`フィールドは削除されたことに注意してください。代わりに、`core`グループの下に`default_agent`フィールドを置く必要があります。例:

```toml
[core]
# その他の設定
default_agent='CodeActAgent'

[agent]
llm_config='llm'
memory_max_threads=2

[agent.CodeActAgent]
llm_config='gpt-4o'
```

`llm`サブグループと同様に、`agent`サブグループも定義できることに注意してください。
さらに、エージェントを特定のLLM設定グループに関連付けることができます。
詳細については、`config.template.toml`の例を参照してください。
