# CLI モード

OpenHands は対話型の CLI モードで実行できます。これにより、ユーザーはコマンドラインから対話型セッションを開始できます。

このモードは、非対話型でスクリプティングに適した [ヘッドレスモード](headless-mode) とは異なります。

## Python を使用する場合

コマンドラインから対話型の OpenHands セッションを開始するには:

1. [開発セットアップの手順](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) に従っていることを確認してください。
2. 以下のコマンドを実行します:

```bash
poetry run python -m openhands.core.cli
```

このコマンドを実行すると、タスクを入力して OpenHands からレスポンスを受け取ることができる対話型セッションが開始されます。

環境変数 [または `config.toml` ファイル](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml) を使用して、モデル、API キー、その他の設定を確実に設定する必要があります。

## Docker を使用する場合

Docker で OpenHands を CLI モードで実行するには:

1. ターミナルで以下の環境変数を設定します:

- `WORKSPACE_BASE` を OpenHands に編集させたいディレクトリに設定 (例: `export WORKSPACE_BASE=$(pwd)/workspace`)。
- `LLM_MODEL` を使用するモデルに設定 (例: `export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`)。
- `LLM_API_KEY` を API キーに設定 (例: `export LLM_API_KEY="sk_test_12345"`)。

2. 以下の Docker コマンドを実行します:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.35-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.35 \
    python -m openhands.core.cli
```

このコマンドを実行すると、Docker 内で対話型セッションが開始され、タスクを入力して OpenHands からレスポンスを受け取ることができます。

## CLI コマンドと期待される出力の例

CLI コマンドとその期待される出力の例を以下に示します:

### 例1: シンプルなタスク

```bash
>> "Hello, World!" と出力する Python スクリプトを書いてください
```

期待される出力:

```bash
🤖 はい! "Hello, World!" と出力する Python スクリプトは以下のようになります:

❯ print("Hello, World!")
```

### 例2: Bash コマンド

```bash
>> "test_dir" という名前のディレクトリを作成してください
```

期待される出力:

```bash
🤖 "test_dir" という名前のディレクトリを作成します:

❯ mkdir test_dir
```

### 例3: エラー処理

```bash
>> 存在しないファイルを削除してください
```

期待される出力:

```bash
🤖 エラーが発生しました。もう一度お試しください。
```
