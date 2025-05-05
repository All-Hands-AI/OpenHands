# Docker ランタイム

これは、OpenHands を起動するときに使用されるデフォルトのランタイムです。

## イメージ
nikolaik の `SANDBOX_RUNTIME_CONTAINER_IMAGE` は、ランタイムサーバーと Python および NodeJS の基本的なユーティリティを含む事前ビルドされたランタイムイメージです。
[独自のランタイムイメージを構築する](../how-to/custom-sandbox-guide)こともできます。

## ファイルシステムへの接続
ここでの便利な機能の1つは、ローカルファイルシステムに接続する機能です。ファイルシステムをランタイムにマウントするには：

### SANDBOX_VOLUMES の使用

ローカルファイルシステムをマウントする最も簡単な方法は、`SANDBOX_VOLUMES` 環境変数を使用することです：

```bash
docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=/path/to/your/code:/workspace:rw \
    # ...
```

`SANDBOX_VOLUMES` の形式は：`ホストパス:コンテナパス[:モード]`

- `ホストパス`：マウントしたいホストマシン上のパス
- `コンテナパス`：ホストパスがマウントされるコンテナ内のパス
  - エージェントに変更させたいファイルには `/workspace` を使用してください。エージェントはデフォルトで `/workspace` で作業します。
  - 読み取り専用の参照資料や大きなデータセットには、別のパス（例：`/data`）を使用してください
- `モード`：オプションのマウントモード、`rw`（読み書き可能、デフォルト）または `ro`（読み取り専用）

カンマ（`,`）で区切ることで、複数のマウントを指定することもできます：

```bash
export SANDBOX_VOLUMES=/path1:/workspace/path1,/path2:/workspace/path2:ro
```

例：

```bash
# Linux と Mac の例 - 書き込み可能なワークスペース
export SANDBOX_VOLUMES=$HOME/OpenHands:/workspace:rw

# Windows の WSL の例 - 書き込み可能なワークスペース
export SANDBOX_VOLUMES=/mnt/c/dev/OpenHands:/workspace:rw

# 読み取り専用参照コードの例
export SANDBOX_VOLUMES=/path/to/reference/code:/data:ro

# 複数マウントの例 - 書き込み可能なワークスペースと読み取り専用データ
export SANDBOX_VOLUMES=$HOME/projects:/workspace:rw,/path/to/large/dataset:/data:ro
```

> **注意：** 複数のマウントを使用する場合、最初のマウントが主要なワークスペースと見なされ、単一のワークスペースを想定するツールとの後方互換性のために使用されます。

> **重要：** エージェントはデフォルトで `/workspace` で作業します。ローカルディレクトリ内のファイルをエージェントに変更させたい場合は、そのディレクトリを `/workspace` にマウントする必要があります。エージェントにアクセスさせたいが変更させたくない読み取り専用データがある場合は、別のパス（例：`/data`）にマウントし、エージェントにそこを見るよう明示的に指示してください。

### WORKSPACE_* 変数の使用（非推奨）

> **注意：** この方法は非推奨であり、将来のバージョンで削除される予定です。代わりに `SANDBOX_VOLUMES` を使用してください。

1. `WORKSPACE_BASE` を設定します：

    ```bash
    export WORKSPACE_BASE=/path/to/your/code
    ```

2. 以下のオプションを `docker run` コマンドに追加します：

    ```bash
    docker run # ...
        -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.36-nikolaik \
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
        -v $WORKSPACE_BASE:/opt/workspace_base \
        # ...
    ```

注意してください！OpenHands エージェントがワークスペースにマウントされたファイルを削除または変更することを妨げるものはありません。

このセットアップはファイルのアクセス権に関する問題を引き起こす可能性がありますが（そのため `SANDBOX_USER_ID` 変数があります）、ほとんどのシステムでうまく機能します。

## 強化された Docker インストール

セキュリティが優先される環境に OpenHands をデプロイする場合は、強化された Docker 構成の実装を検討する必要があります。このセクションでは、デフォルト構成を超えて OpenHands Docker デプロイメントを保護するための推奨事項を提供します。

### セキュリティに関する考慮事項

README のデフォルトの Docker 構成は、ローカル開発マシンでの使いやすさを考慮して設計されています。公共ネットワーク（例：空港の WiFi）で実行している場合は、追加のセキュリティ対策を実装する必要があります。

### ネットワークバインディングのセキュリティ

デフォルトでは、OpenHands はすべてのネットワークインターフェース（`0.0.0.0`）にバインドされ、ホストが接続しているすべてのネットワークにインスタンスが公開される可能性があります。より安全なセットアップのために：

1. **ネットワークバインディングの制限**：

   `runtime_binding_address` 構成を使用して、OpenHands がリッスンするネットワークインターフェースを制限します：

   ```bash
   docker run # ...
       -e SANDBOX_RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       # ...
   ```

   この構成により、OpenHands はループバックインターフェース（`127.0.0.1`）でのみリッスンし、ローカルマシンからのみアクセス可能になります。

2. **ポートバインディングの保護**：

   `-p` フラグを変更して、すべてのインターフェースではなくローカルホストにのみバインドします：

   ```bash
   docker run # ... \
       -p 127.0.0.1:3000:3000 \
   ```

   これにより、OpenHands ウェブインターフェースはローカルマシンからのみアクセス可能になり、ネットワーク上の他のマシンからはアクセスできなくなります。

### ネットワーク分離

Docker のネットワーク機能を使用して OpenHands を分離します：

```bash
# 分離されたネットワークを作成
docker network create openhands-network

# 分離されたネットワークで OpenHands を実行
docker run # ... \
    --network openhands-network \
    docker.all-hands.dev/all-hands-ai/openhands:0.36
```
