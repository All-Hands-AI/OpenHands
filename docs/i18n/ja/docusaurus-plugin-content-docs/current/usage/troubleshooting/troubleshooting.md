# 🚧 トラブルシューティング

:::tip
OpenHandsはWSL経由でのみWindowsをサポートしています。必ずWSLターミナル内でコマンドを実行してください。
:::

### Dockerクライアントの起動に失敗

**説明**

OpenHandsを実行する際に、以下のようなエラーが表示される:
```
Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.
```

**解決策**

以下の順番で試してみてください:
* システム上で`docker`が実行されていることを確認します。ターミナルで`docker ps`が正常に実行できるはずです。
* Docker Desktopを使用している場合は、`Settings > Advanced > Allow the default Docker socket to be used`が有効になっていることを確認してください。
* 設定によっては、Docker Desktopで`Settings > Resources > Network > Enable host networking`を有効にする必要があるかもしれません。
* Docker Desktopを再インストールしてみてください。
---

# 開発ワークフロー固有の問題
### runtimeのDockerイメージのビルドエラー

**説明**

新しいセッションの開始に失敗し、ログに以下のようなエラーが表示される:
```
debian-security bookworm-security
InRelease At least one invalid signature was encountered.
```

これは、既存の外部ライブラリのハッシュが変更され、ローカルのDockerインスタンスが以前のバージョンをキャッシュしている場合に発生するようです。これを回避するには、以下を試してみてください:

* 名前が`openhands-runtime-`で始まるコンテナを停止します:
  `docker ps --filter name=openhands-runtime- --filter status=running -aq | xargs docker stop`
* 名前が`openhands-runtime-`で始まるコンテナを削除します:
  `docker rmi $(docker images --filter name=openhands-runtime- -q --no-trunc)`
* 名前が`openhands-runtime-`で始まるコンテナ/イメージを停止して削除します
* コンテナ/イメージをプルーンします: `docker container prune -f && docker image prune -f`
