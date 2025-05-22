# ヘッドレスモード

OpenHandsは、Webアプリケーションを起動せずに単一のコマンドで実行できます。
これにより、スクリプトを作成してOpenHandsでタスクを自動化することが容易になります。

これは対話型で、アクティブな開発に適している[CLIモード](cli-mode)とは異なります。

## Pythonでの実行

PythonでヘッドレスモードでOpenHandsを実行するには：
1. [開発セットアップ手順](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)に従っていることを確認してください。
2. 次のコマンドを実行します：
```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

環境変数または[`config.toml`ファイル](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)を通じて、モデル、APIキー、その他の設定を必ず設定してください。

## Dockerでの実行

DockerでヘッドレスモードでOpenHandsを実行するには：

1. ターミナルで次の環境変数を設定します：

- `SANDBOX_VOLUMES`でOpenHandsがアクセスするディレクトリを指定します（例：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw`）。
  - エージェントはデフォルトで`/workspace`で作業するため、エージェントにファイルを変更させたい場合はプロジェクトディレクトリをそこにマウントします。
  - 読み取り専用データの場合は、異なるマウントパスを使用します（例：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw,/path/to/large/dataset:/data:ro`）。
- `LLM_MODEL`に使用するモデルを設定します（例：`export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`）。
- `LLM_API_KEY`にAPIキーを設定します（例：`export LLM_API_KEY="sk_test_12345"`）。

2. 次のDockerコマンドを実行します：

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.39 \
    python -m openhands.core.main -t "write a bash script that prints hi"
```

`-e SANDBOX_USER_ID=$(id -u)`はDockerコマンドに渡され、サンドボックスユーザーがホストユーザーの権限と一致するようにします。これにより、エージェントがマウントされたワークスペースにroot所有のファイルを作成するのを防ぎます。

## 高度なヘッドレス設定

ヘッドレスモードで利用可能なすべての設定オプションを表示するには、Pythonコマンドに`--help`フラグを付けて実行します。

### 追加ログ

ヘッドレスモードですべてのエージェントアクションをログに記録するには、ターミナルで次のコマンドを実行します：`export LOG_ALL_EVENTS=true`
