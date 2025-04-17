# Docker ランタイム

これは、OpenHands を起動するときに使用されるデフォルトのランタイムです。

## イメージ
nikolaik の `SANDBOX_RUNTIME_CONTAINER_IMAGE` は、ランタイムサーバーと Python および NodeJS の基本的なユーティリティを含む事前ビルドされたランタイムイメージです。
[独自のランタイムイメージを構築する](../how-to/custom-sandbox-guide)こともできます。

## ファイルシステムへの接続
ここでの便利な機能の1つは、ローカルファイルシステムに接続する機能です。ファイルシステムをランタイムにマウントするには：
1. `WORKSPACE_BASE` を設定します：

    ```bash
    export WORKSPACE_BASE=/path/to/your/code

    # Linux と Mac の例
    # export WORKSPACE_BASE=$HOME/OpenHands
    # $WORKSPACE_BASE を /home/<username>/OpenHands に設定します
    #
    # Windows の WSL の例
    # export WORKSPACE_BASE=/mnt/c/dev/OpenHands
    # $WORKSPACE_BASE を C:\dev\OpenHands に設定します
    ```
2. 以下のオプションを `docker run` コマンドに追加します：

    ```bash
    docker run # ...
        -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.33-nikolaik \
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
    docker.all-hands.dev/all-hands-ai/openhands:0.33
```
