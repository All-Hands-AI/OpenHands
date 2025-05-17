# Python API

OpenHandsは、Pythonコードから直接使用できる豊富なAPIを提供しています。以下は、主要なAPIの概要です。

## OpenHands クライアント

```python
from openhands import OpenHandsClient

# クライアントの初期化
client = OpenHandsClient(
    api_key="your-api-key",  # OpenAI APIキーなど
    model="gpt-4",           # 使用するLLMモデル
    workspace="/path/to/workspace"  # 作業ディレクトリ
)

# タスクの実行
result = client.execute_task("新しいPythonファイルを作成してください")

# 結果の取得
print(result.success)  # タスクが成功したかどうか
print(result.output)   # タスクの出力
print(result.error)    # エラーメッセージ（存在する場合）
```

## サンドボックス設定

```python
from openhands import SandboxConfig

# サンドボックス設定のカスタマイズ
config = SandboxConfig(
    allowed_commands=["git", "python"],  # 許可するコマンド
    timeout=300,                         # タイムアウト（秒）
    max_memory="2g",                     # メモリ制限
    network_access=True                  # ネットワークアクセスの許可
)

# 設定を使用してクライアントを初期化
client = OpenHandsClient(
    api_key="your-api-key",
    model="gpt-4",
    workspace="/path/to/workspace",
    sandbox_config=config
)
```

## イベントハンドリング

```python
from openhands import OpenHandsClient

def on_progress(event):
    print(f"進捗: {event.message}")

def on_error(event):
    print(f"エラー: {event.error}")

# イベントハンドラーを設定してクライアントを初期化
client = OpenHandsClient(
    api_key="your-api-key",
    model="gpt-4",
    workspace="/path/to/workspace",
    on_progress=on_progress,
    on_error=on_error
)
```

## 非同期API

```python
import asyncio
from openhands import AsyncOpenHandsClient

async def main():
    # 非同期クライアントの初期化
    client = AsyncOpenHandsClient(
        api_key="your-api-key",
        model="gpt-4",
        workspace="/path/to/workspace"
    )

    # タスクの非同期実行
    result = await client.execute_task("新しいPythonファイルを作成してください")
    print(result.output)

# 非同期メインの実行
asyncio.run(main())
