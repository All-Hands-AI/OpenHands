# Dockerランタイム

これは、OpenHandsを起動する際にデフォルトで使用されるランタイムです。

## イメージ
nikolaikからの`SANDBOX_RUNTIME_CONTAINER_IMAGE`は、ランタイムサーバーと、PythonとNodeJSの基本的なユーティリティを含む事前ビルドされたランタイムイメージです。
[独自のランタイムイメージを構築する](../how-to/custom-sandbox-guide)こともできます。

## ファイルシステムへの接続
便利な機能の一つは、ローカルファイルシステムに接続する機能です。ランタイムにファイルシステムをマウントするには：

### SANDBOX_VOLUMESの使用

ローカルファイルシステムをマウントする最も簡単な方法は、`SANDBOX_VOLUMES`環境変数を使用することです：

```bash
docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=/path/to/your/code:/workspace:rw \
    # ...
```

`SANDBOX_VOLUMES`のフォーマットは：`host_path:container_path[:mode]`

- `host_path`：マウントしたいホストマシン上のパス
- `container_path`：ホストパスがマウントされるコンテナ内のパス
  - エージェントに変更させたいファイルには`/workspace`を使用します。エージェントはデフォルトで`/workspace`で作業します。
  - 読み取り専用の参照資料や大きなデータセットには、別のパス（例：`/data`）を使用します。
- `mode`：オプションのマウントモード、`rw`（読み書き、デフォルト）または`ro`（読み取り専用）

カンマ（`,`）で区切ることで、複数のマウントを指定することもできます：

```bash
export SANDBOX_VOLUMES=/path1:/workspace/path1,/path2:/workspace/path2:ro
```

例：

```bash
# LinuxとMacの例 - 書き込み可能なワークスペース
export SANDBOX_VOLUMES=$HOME/OpenHands:/workspace:rw

# Windows上のWSLの例 - 書き込み可能なワークスペース
export SANDBOX_VOLUMES=/mnt/c/dev/OpenHands:/workspace:rw

# 読み取り専用の参照コードの例
export SANDBOX_VOLUMES=/path/to/reference/code:/data:ro

# 複数マウントの例 - 書き込み可能なワークスペースと読み取り専用の参照データ
export SANDBOX_VOLUMES=$HOME/projects:/workspace:rw,/path/to/large/dataset:/data:ro
```

> **注意：** 複数のマウントを使用する場合、最初のマウントが主要なワークスペースと見なされ、単一のワークスペースを想定するツールとの後方互換性のために使用されます。

> **重要：** エージェントはデフォルトで`/workspace`で作業します。エージェントにローカルディレクトリ内のファイルを変更させたい場合は、そのディレクトリを`/workspace`にマウントする必要があります。エージェントにアクセスさせたいが変更させたくない読み取り専用データがある場合は、別のパス（`/data`など）にマウントし、エージェントにそこを見るよう明示的に指示してください。

### WORKSPACE_*変数の使用（非推奨）

> **注意：** この方法は非推奨であり、将来のバージョンで削除される予定です。代わりに`SANDBOX_VOLUMES`を使用してください。

1. `WORKSPACE_BASE`を設定します：

    ```bash
    export WORKSPACE_BASE=/path/to/your/code
    ```

2. `docker run`コマンドに以下のオプションを追加します：

    ```bash
    docker run # ...
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
        -v $WORKSPACE_BASE:/opt/workspace_base \
        # ...
    ```

注意してください！OpenHandsエージェントがワークスペースにマウントされたファイルを削除または変更することを防ぐものは何もありません。

`-e SANDBOX_USER_ID=$(id -u)`はDockerコマンドに渡され、サンドボックスユーザーがホストユーザーの権限と一致するようにします。これにより、エージェントがマウントされたワークスペースにroot所有のファイルを作成することを防ぎます。

## 強化されたDockerインストール

セキュリティが優先される環境でOpenHandsをデプロイする場合、強化されたDockerの設定を検討すべきです。このセクションでは、デフォルト設定を超えてOpenHandsのDockerデプロイメントを保護するための推奨事項を提供します。

### セキュリティの考慮事項

READMEのデフォルトのDocker設定は、ローカル開発マシンでの使いやすさを考慮して設計されています。公共ネットワーク（例：空港のWiFi）で実行している場合は、追加のセキュリティ対策を実施する必要があります。

### ネットワークバインディングのセキュリティ

デフォルトでは、OpenHandsはすべてのネットワークインターフェース（`0.0.0.0`）にバインドし、ホストが接続しているすべてのネットワークにインスタンスを公開する可能性があります。より安全な設定のために：

1. **ネットワークバインディングの制限**：`runtime_binding_address`設定を使用して、OpenHandsがリッスンするネットワークインターフェースを制限します：

   ```bash
   docker run # ...
       -e SANDBOX_RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       # ...
   ```

   この設定により、OpenHandsはループバックインターフェース（`127.0.0.1`）のみでリッスンし、ローカルマシンからのみアクセス可能になります。

2. **ポートバインディングの保護**：`-p`フラグを変更して、すべてのインターフェースではなくlocalhostにのみバインドします：

   ```bash
   docker run # ... \
       -p 127.0.0.1:3000:3000 \
   ```

   これにより、OpenHandsのWebインターフェースはローカルマシンからのみアクセス可能になり、ネットワーク上の他のマシンからはアクセスできなくなります。

### ネットワーク分離

Dockerのネットワーク機能を使用してOpenHandsを分離します：

```bash
# 分離されたネットワークを作成
docker network create openhands-network

# 分離されたネットワークでOpenHandsを実行
docker run # ... \
    --network openhands-network \
```
