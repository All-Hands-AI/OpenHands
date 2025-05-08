# 🚧 トラブルシューティング

:::tip
OpenHandsはWindowsではWSL経由でのみサポートされています。すべてのコマンドはWSLターミナル内で実行してください。
:::

### ローカルIPを介してVS Codeタブにアクセスできない

**説明**

OpenHandsをlocalhostではないURL（LANのIPアドレスなど）を通じてアクセスすると、VS Codeタブに「Forbidden」エラーが表示されますが、UIの他の部分は正常に動作します。

**解決策**

これは、VS Codeがランダムな高ポートで実行され、他のマシンからアクセスできないか公開されていない可能性があるために発生します。修正するには：

1. `SANDBOX_VSCODE_PORT`環境変数を使用して、VS Code用の特定のポートを設定します：
   ```bash
   docker run -it --rm \
       -e SANDBOX_VSCODE_PORT=41234 \
       -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:latest \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.openhands-state:/.openhands-state \
       -p 3000:3000 \
       -p 41234:41234 \
       --add-host host.docker.internal:host-gateway \
       --name openhands-app \
       docker.all-hands.dev/all-hands-ai/openhands:latest
   ```

2. Dockerコマンドで同じポートを`-p 41234:41234`で公開していることを確認してください。

3. または、`config.toml`ファイルで設定することもできます：
   ```toml
   [sandbox]
   vscode_port = 41234
   ```

### Dockerクライアントの起動に失敗

**説明**

OpenHandsを実行すると、次のエラーが表示されます：
```
Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.
```

**解決策**

以下を順番に試してください：
* システム上で`docker`が実行されていることを確認します。ターミナルで`docker ps`を正常に実行できるはずです。
* Docker Desktopを使用している場合は、`設定 > 詳細 > デフォルトのDockerソケットの使用を許可する`が有効になっていることを確認してください。
* 構成によっては、Docker Desktopの`設定 > リソース > ネットワーク > ホストネットワーキングを有効にする`を有効にする必要がある場合があります。
* Docker Desktopを再インストールしてください。

### 権限エラー

**説明**

最初のプロンプトで、`Permission Denied`または`PermissionError`というエラーが表示されます。

**解決策**

* `~/.openhands-state`が`root`によって所有されているかどうかを確認してください。もしそうなら：
  * ディレクトリの所有権を変更します：`sudo chown <user>:<user> ~/.openhands-state`
  * またはディレクトリの権限を更新します：`sudo chmod 777 ~/.openhands-state`
  * または以前のデータが必要ない場合は削除します。OpenHandsは再作成します。LLM設定を再入力する必要があります。
* ローカルディレクトリをマウントしている場合は、`WORKSPACE_BASE`にOpenHandsを実行しているユーザーに必要な権限があることを確認してください。
