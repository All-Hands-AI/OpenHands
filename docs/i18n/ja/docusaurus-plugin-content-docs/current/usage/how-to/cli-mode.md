# CLIモード

OpenHandsは対話型CLIモードで実行でき、コマンドラインを通じて対話型セッションを開始することができます。

このモードは[ヘッドレスモード](headless-mode)とは異なり、対話型であり、スクリプト実行よりもユーザー操作に適しています。

## Pythonでの実行

コマンドラインから対話型OpenHandsセッションを開始するには：

1. [開発環境セットアップ手順](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)に従っていることを確認してください。
2. 以下のコマンドを実行します：

```bash
poetry run python -m openhands.core.cli
```

このコマンドは対話型セッションを開始し、タスクを入力してOpenHandsからの応答を受け取ることができます。

環境変数または[`config.toml`ファイル](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)を通じて、モデル、APIキー、その他の設定を確実に設定する必要があります。

## Dockerでの実行

DockerでOpenHandsをCLIモードで実行するには：

1. ターミナルで以下の環境変数を設定します：

- `SANDBOX_VOLUMES`でOpenHandsがアクセスするディレクトリを指定します（例：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw`）。
  - エージェントはデフォルトで`/workspace`で動作するため、エージェントにファイルを変更させたい場合はプロジェクトディレクトリをそこにマウントします。
  - 読み取り専用データの場合は、異なるマウントパスを使用します（例：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw,/path/to/large/dataset:/data:ro`）。
- `LLM_MODEL`に使用するモデルを設定します（例：`export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`）。
- `LLM_API_KEY`にAPIキーを設定します（例：`export LLM_API_KEY="sk_test_12345"`）。

2. 以下のDockerコマンドを実行します：

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.39 \
    python -m openhands.core.cli
```

このコマンドはDocker内で対話型セッションを開始し、タスクを入力してOpenHandsからの応答を受け取ることができます。

`-e SANDBOX_USER_ID=$(id -u)`はDockerコマンドに渡され、サンドボックスユーザーがホストユーザーの権限と一致するようにします。これにより、エージェントがマウントされたワークスペースにroot所有のファイルを作成するのを防ぎます。
