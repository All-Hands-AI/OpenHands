# ローカルランタイム

ローカルランタイムを使用すると、OpenHands エージェントは Docker を使用せずに直接ローカルマシン上でアクションを実行できます。このランタイムは主に、Docker が利用できない CI パイプラインやテストシナリオなどの制御された環境向けです。

:::caution
**セキュリティ警告**: ローカルランタイムはサンドボックス分離なしで実行されます。エージェントはマシン上のファイルに直接アクセスして変更できます。制御された環境でのみ、またはセキュリティへの影響を十分に理解している場合にのみ、このランタイムを使用してください。
:::

## 前提条件

ローカルランタイムを使用する前に、以下を確認してください：

1. [開発セットアップ手順](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)に従っていること。
2. tmux がシステムで利用可能であること。

## 設定

ローカルランタイムを使用するには、モデル、API キーなどの必要な設定に加えて、OpenHands を起動するときに環境変数または[config.toml ファイル](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)を介して以下のオプションを設定する必要があります：

- 環境変数を介して：

```bash
# 必須
export RUNTIME=local

# オプションですが推奨
export WORKSPACE_BASE=/path/to/your/workspace
```

- `config.toml` を介して：

```toml
[core]
runtime = "local"
workspace_base = "/path/to/your/workspace"
```

`WORKSPACE_BASE` が設定されていない場合、ランタイムはエージェントが作業するための一時ディレクトリを作成します。

## 使用例

以下は、ヘッドレスモードでローカルランタイムを使用して OpenHands を起動する例です：

```bash
# ランタイムタイプをローカルに設定
export RUNTIME=local

# オプションでワークスペースディレクトリを設定
export WORKSPACE_BASE=/path/to/your/project

# OpenHands を起動
poetry run python -m openhands.core.main -t "hi と出力する bash スクリプトを書いてください"
```

## ユースケース

ローカルランタイムは特に以下の場合に役立ちます：

- Docker が利用できない CI/CD パイプライン。
- OpenHands 自体のテストと開発。
- コンテナの使用が制限されている環境。
- ファイルシステムへの直接アクセスが必要なシナリオ。
