# ローカルLLMとOllama

:::warning
ローカルLLMを使用する場合、OpenHandsの機能が制限される可能性があります。
:::

Ollamaサーバーが起動し、実行中であることを確認してください。
詳細な起動手順については、[こちら](https://github.com/ollama/ollama)を参照してください。

このガイドでは、`ollama serve`でollamaを起動したことを前提としています。ollamaを別の方法で実行している場合（例：dockerの中で）、手順を変更する必要があるかもしれません。WSLを実行している場合、デフォルトのollama設定ではdockerコンテナからのリクエストがブロックされることに注意してください。[こちら](#configuring-ollama-service-wsl-ja)を参照してください。

## モデルのプル

Ollamaモデル名は[こちら](https://ollama.com/library)で確認できます。小さな例として、`codellama:7b`モデルを使用できます。一般的に、より大きなモデルの方が性能が良くなります。

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

## DockerでOpenHandsを実行

### OpenHandsの起動
[こちら](../getting-started)の手順を使用して、DockerでOpenHandsを起動します。
ただし、`docker run`を実行する際に、いくつかの引数を追加する必要があります：

```bash
docker run # ...
    --add-host host.docker.internal:host-gateway \
    -e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    # ...
```

LLM_OLLAMA_BASE_URLはオプションです。設定すると、UIでインストール済みの利用可能なモデルを表示するために使用されます。


### Webアプリケーションの設定

`openhands`を実行する際、OpenHands UIの設定で以下を設定する必要があります：
- モデルを"ollama/&lt;model-name&gt;"に
- ベースURLを`http://host.docker.internal:11434`に
- APIキーはオプションで、`ollama`などの任意の文字列を使用できます。


## 開発モードでOpenHandsを実行

### ソースからビルド

[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)の手順を使用して、OpenHandsをビルドします。
`make setup-config`を実行して`config.toml`が存在することを確認してください。これにより、設定ファイルが作成されます。`config.toml`に以下を入力します：

```
[core]
workspace_base="./workspace"

[llm]
embedding_model="local"
ollama_base_url="http://localhost:11434"

```

これで完了です！`make run`でOpenHandsを起動できるようになりました。`http://localhost:3000/`に接続できるはずです。

### Webアプリケーションの設定

OpenHands UIで、左下の設定ホイールをクリックします。
次に、`Model`入力に`ollama/codellama:7b`、または先ほどプルしたモデルの名前を入力します。
ドロップダウンに表示されない場合は、`Advanced Settings`を有効にして入力してください。注意：`ollama list`で表示されるモデル名に、接頭辞`ollama/`を付ける必要があります。

APIキーフィールドには、特定のキーが不要なので、`ollama`または任意の値を入力します。

ベースURLフィールドには、`http://localhost:11434`を入力します。

これで準備完了です！

## ollamaサービスの設定（WSL） {#configuring-ollama-service-wsl-ja}

WSLのollamaのデフォルト設定では、localhostのみにサービスを提供します。つまり、dockerコンテナからアクセスできません。例えば、OpenHandsでは動作しません。まず、ollamaが正しく実行されていることをテストしましょう。

```bash
ollama list # インストール済みモデルのリストを取得
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例 curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#例 curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #タグは1つしかない場合はオプション
```

完了したら、dockerコンテナ内からの「外部」リクエストを許可するかテストします。

```bash
docker ps # 実行中のdockerコンテナのリストを取得。最も正確なテストのためにOpenHandsサンドボックスコンテナを選択。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例 docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## 修正方法

それでは、動作するようにしましょう。sudo権限で/etc/systemd/system/ollama.serviceを編集します。（パスはLinuxの種類によって異なる場合があります）

```bash
sudo vi /etc/systemd/system/ollama.service
```

または

```bash
sudo nano /etc/systemd/system/ollama.service
```

[Service]ブラケットにこれらの行を追加します

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

そして保存し、設定をリロードしてサービスを再起動します。

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

最後に、コンテナ内からollamaにアクセスできることをテストします

```bash
ollama list # インストール済みモデルのリストを取得
docker ps # 実行中のdockerコンテナのリストを取得。最も正確なテストのためにOpenHandsサンドボックスコンテナを選択。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```


# ローカルLLMとLM Studio

LM Studioのセットアップ手順：
1. LM Studioを開きます
2. ローカルサーバータブに移動します。
3. 「サーバーを起動」ボタンをクリックします。
4. ドロップダウンから使用するモデルを選択します。


以下の設定を行います：
```bash
LLM_MODEL="openai/lmstudio"
LLM_BASE_URL="http://localhost:1234/v1"
CUSTOM_LLM_PROVIDER="openai"
```

### Docker

```bash
docker run # ...
    -e LLM_MODEL="openai/lmstudio" \
    -e LLM_BASE_URL="http://host.docker.internal:1234/v1" \
    -e CUSTOM_LLM_PROVIDER="openai" \
    # ...
```

これで、`http://localhost:3000/`に接続できるはずです。

開発環境では、`config.toml`ファイルに以下の設定を行うことができます：

```
[core]
workspace_base="./workspace"

[llm]
model="openai/lmstudio"
base_url="http://localhost:1234/v1"
custom_llm_provider="openai"
```

完了です！これで、Dockerなしで`make run`を実行してOpenHandsを起動できます。`http://localhost:3000/`に接続できるはずです。

# 注意

WSLの場合、cmdで以下のコマンドを実行して、ネットワークモードをミラーに設定します：

```
python -c  "print('[wsl2]\nnetworkingMode=mirrored',file=open(r'%UserProfile%\.wslconfig','w'))"
wsl --shutdown
```
