# Ollama を使用したローカル LLM

Ollama サーバーが実行中であることを確認してください。
詳細な起動手順については、[こちら](https://github.com/ollama/ollama)を参照してください。

このガイドでは、`ollama serve` で ollama を起動していることを前提としています。ollama を別の方法で実行している場合（例えば、docker 内で実行している場合）、手順を変更する必要があるかもしれません。WSL を使用している場合、ollama のデフォルト設定では docker コンテナからのリクエストがブロックされることに注意してください。[こちら](#configuring-ollama-service-ja)を参照してください。

## モデルのダウンロード

Ollama のモデル名は[こちら](https://ollama.com/library)で確認できます。小さなサンプルとしては、`codellama:7b` モデルを使用できます。一般的に、より大きなモデルの方がパフォーマンスが良くなります。

```bash
ollama pull codellama:7b
```

ダウンロードしたモデルは以下のように確認できます：

```bash
~$ ollama list
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## OpenHands の起動

### Docker

[こちら](../intro)の手順を使用して、Docker で OpenHands を起動します。
ただし、`docker run` を実行する際に、いくつかの追加引数が必要になります：

```bash
--add-host host.docker.internal:host-gateway \
-e LLM_API_KEY="ollama" \
-e LLM_BASE_URL="http://host.docker.internal:11434" \
```

例：

```bash
# OpenHands に変更させたいディレクトリ。絶対パスでなければなりません！
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -it \
    --pull=always \
    --add-host host.docker.internal:host-gateway \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_API_KEY="ollama" \
    -e LLM_BASE_URL="http://host.docker.internal:11434" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/all-hands-ai/openhands:main
```

これで `http://localhost:3000/` に接続できるはずです。

### ソースからのビルド

[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) の手順を使用して、OpenHands をビルドします。
`make setup-config` を実行して `config.toml` が存在することを確認してください。これにより、`config.toml` が作成されます。`config.toml` に以下を入力します：

```
LLM_MODEL="ollama/codellama:7b"
LLM_API_KEY="ollama"
LLM_EMBEDDING_MODEL="local"
LLM_BASE_URL="http://localhost:11434"
WORKSPACE_BASE="./workspace"
WORKSPACE_DIR="$(pwd)/workspace"
```

必要に応じて、`LLM_MODEL` を選択したものに置き換えてください。

以上で完了です！これで、Docker なしで `make run` を使用して OpenHands を起動できます。`http://localhost:3000/` に接続できるはずです。

## モデルの選択

OpenHands のインターフェースで、左下の設定アイコンをクリックします。
次に、`Model` の入力欄に `ollama/codellama:7b` または先ほどダウンロードしたモデル名を入力します。
ドロップダウンメニューに表示されなくても問題ありません。そのまま入力してください。完了したら、保存をクリックします。

これで、開始する準備が整いました！

## ollama サービスの設定 (WSL){#configuring-ollama-service-ja}

WSL 上の ollama のデフォルト設定では、localhost のみが提供されます。つまり、docker コンテナなどから到達できないため、OpenHands では動作しません。まず、ollama が正しく実行されているかテストしてみましょう。

```bash
ollama list # インストールされているモデルのリストを取得
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例 curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#例 curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #タグは1つしかない場合はオプション
```

これが完了したら、docker コンテナなどからの「外部」リクエストを受け入れるかどうかをテストします。

```bash
docker ps # 実行中の docker コンテナのリストを取得。最も正確なテストのために OpenHands サンドボックスコンテナを選択。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例 docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## 修正

これで動作するようにしましょう。sudo 権限で /etc/systemd/system/ollama.service を編集します。（パスは Linux ディストリビューションによって異なる場合があります）

```bash
sudo vi /etc/systemd/system/ollama.service
```

または

```bash
sudo nano /etc/systemd/system/ollama.service
```

[Service] セクションに、以下の行を追加します

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

次に、保存し、設定をリロードしてサービスを再起動します。

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

最後に、コンテナから ollama にアクセスできることをテストします

```bash
ollama list # インストールされているモデルのリストを取得
docker ps # 実行中の docker コンテナのリストを取得。最も正確なテストのために OpenHands サンドボックスコンテナを選択。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```
