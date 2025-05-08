# モデルコンテキストプロトコル（MCP）

:::note
このページでは、OpenHandsでモデルコンテキストプロトコル（MCP）を設定して使用する方法を説明します。これにより、エージェントの機能をカスタムツールで拡張できます。
:::

## 概要

モデルコンテキストプロトコル（MCP）は、OpenHandsが外部ツールサーバーと通信するためのメカニズムです。これらのサーバーは、特殊なデータ処理、外部APIアクセス、またはカスタムツールなど、エージェントに追加機能を提供できます。MCPは[modelcontextprotocol.io](https://modelcontextprotocol.io)で定義されているオープンスタンダードに基づいています。

## 設定

MCP設定は`config.toml`ファイルの`[mcp]`セクションで定義されます。

### 設定例

```toml
[mcp]
# SSEサーバー - Server-Sent Eventsを介して通信する外部サーバー
sse_servers = [
    # 基本的なSSEサーバー（URLのみ）
    "http://example.com:8080/mcp",

    # APIキー認証を使用するSSEサーバー
    {url="https://secure-example.com/mcp", api_key="your-api-key"}
]

# Stdioサーバー - 標準入出力を介して通信するローカルプロセス
stdio_servers = [
    # 基本的なstdioサーバー
    {name="fetch", command="uvx", args=["mcp-server-fetch"]},

    # 環境変数を持つstdioサーバー
    {
        name="data-processor",
        command="python",
        args=["-m", "my_mcp_server"],
        env={
            "DEBUG": "true",
            "PORT": "8080"
        }
    }
]
```

## 設定オプション

### SSEサーバー

SSEサーバーは、文字列URLまたは以下のプロパティを持つオブジェクトを使用して設定されます：

- `url`（必須）
  - 型: `str`
  - 説明: SSEサーバーのURL

- `api_key`（オプション）
  - 型: `str`
  - デフォルト: `None`
  - 説明: SSEサーバーとの認証用APIキー

### Stdioサーバー

Stdioサーバーは、以下のプロパティを持つオブジェクトを使用して設定されます：

- `name`（必須）
  - 型: `str`
  - 説明: サーバーの一意の名前

- `command`（必須）
  - 型: `str`
  - 説明: サーバーを実行するコマンド

- `args`（オプション）
  - 型: `list of str`
  - デフォルト: `[]`
  - 説明: サーバーに渡すコマンドライン引数

- `env`（オプション）
  - 型: `dict of str to str`
  - デフォルト: `{}`
  - 説明: サーバープロセスに設定する環境変数

## MCPの仕組み

OpenHandsが起動すると、次のことが行われます：

1. `config.toml`からMCP設定を読み込む
2. 設定されたSSEサーバーに接続する
3. 設定されたstdioサーバーを起動する
4. これらのサーバーが提供するツールをエージェントに登録する

エージェントは、これらのツールを組み込みツールと同じように使用できます。エージェントがMCPツールを呼び出すと：

1. OpenHandsは呼び出しを適切なMCPサーバーにルーティングする
2. サーバーはリクエストを処理し、レスポンスを返す
3. OpenHandsはレスポンスを観察結果に変換し、エージェントに提示する
