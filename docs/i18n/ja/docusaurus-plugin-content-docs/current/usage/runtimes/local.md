# ローカルランタイム

ローカルランタイムを使用すると、OpenHandsエージェントはDockerを使用せずに直接ローカルマシン上でアクションを実行できます。
このランタイムは主に、Dockerが利用できないCI（継続的インテグレーション）パイプラインやテストシナリオなどの制御された環境向けに設計されています。

:::caution
**セキュリティ警告**: ローカルランタイムはサンドボックス分離なしで実行されます。エージェントはマシン上のファイルに直接アクセスして変更することができます。このランタイムは、制御された環境または安全性の影響を十分に理解している場合にのみ使用してください。
:::

## 前提条件

ローカルランタイムを使用する前に、以下を確認してください：

1. [開発ワークフロー](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)を使用してOpenHandsを実行できること。
2. システム上でtmuxが利用可能であること。

## 設定

ローカルランタイムを使用するには、LLMプロバイダー、モデル、APIキーなどの必要な設定に加えて、OpenHandsを起動する際に環境変数または[config.tomlファイル](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)を通じて以下のオプションを設定する必要があります：

環境変数を使用する場合：

```bash
# 必須
export RUNTIME=local

# オプションですが推奨
# エージェントはデフォルトで/workspaceで作業するため、プロジェクトディレクトリをそこにマウントします
export SANDBOX_VOLUMES=/path/to/your/workspace:/workspace:rw
# 読み取り専用データの場合は、異なるマウントパスを使用します
# export SANDBOX_VOLUMES=/path/to/your/workspace:/workspace:rw,/path/to/large/dataset:/data:ro
```

`config.toml`を使用する場合：

```toml
[core]
runtime = "local"

[sandbox]
# エージェントはデフォルトで/workspaceで作業するため、プロジェクトディレクトリをそこにマウントします
volumes = "/path/to/your/workspace:/workspace:rw"
# 読み取り専用データの場合は、異なるマウントパスを使用します
# volumes = "/path/to/your/workspace:/workspace:rw,/path/to/large/dataset:/data:ro"
```

`SANDBOX_VOLUMES`が設定されていない場合、ランタイムはエージェントが作業するための一時ディレクトリを作成します。

## 使用例

以下は、ヘッドレスモードでローカルランタイムを使用してOpenHandsを起動する例です：

```bash
# ランタイムタイプをlocalに設定
export RUNTIME=local

# ワークスペースディレクトリを設定（エージェントはデフォルトで/workspaceで作業します）
export SANDBOX_VOLUMES=/path/to/your/project:/workspace:rw
# エージェントに変更させたくない読み取り専用データの場合は、異なるパスを使用します
# export SANDBOX_VOLUMES=/path/to/your/project:/workspace:rw,/path/to/reference/data:/data:ro

# OpenHandsを起動
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

## ユースケース

ローカルランタイムは特に以下の場合に役立ちます：

- Dockerが利用できないCI/CDパイプライン。
- OpenHands自体のテストと開発。
- コンテナの使用が制限されている環境。
