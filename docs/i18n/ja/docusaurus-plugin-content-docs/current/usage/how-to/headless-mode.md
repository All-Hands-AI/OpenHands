# ヘッドレスモード

OpenHandsは、Webアプリケーションを起動せずに、単一のコマンドで実行できます。
これにより、OpenHandsを使用してスクリプトを作成したり、タスクを自動化したりするのが簡単になります。

これは、インタラクティブで、アクティブな開発に適した[CLIモード](cli-mode)とは異なります。

## Pythonを使用する場合

PythonでOpenHandsをヘッドレスモードで実行するには:
1. [開発セットアップの手順](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)に従っていることを確認してください。
2. 以下のコマンドを実行します:
```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

モデル、APIキー、その他の設定は、環境変数[または`config.toml`ファイル](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)を介して設定する必要があります。

## Dockerを使用する場合

DockerでOpenHandsをヘッドレスモードで実行するには:

1. ターミナルで以下の環境変数を設定します:

- `WORKSPACE_BASE`をOpenHandsが編集するディレクトリに設定 (例: `export WORKSPACE_BASE=$(pwd)/workspace`)。
- `LLM_MODEL`を使用するモデルに設定 (例: `export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`)。
- `LLM_API_KEY`をAPIキーに設定 (例: `export LLM_API_KEY="sk_test_12345"`)。

2. 以下のDockerコマンドを実行します:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.35-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.35 \
    python -m openhands.core.main -t "write a bash script that prints hi"
```

## 高度なヘッドレス設定

ヘッドレスモードで利用可能なすべての設定オプションを表示するには、`--help`フラグを付けてPythonコマンドを実行します。

### 追加のログ

ヘッドレスモードでエージェントのすべてのアクションをログに記録するには、ターミナルで`export LOG_ALL_EVENTS=true`を実行します。
