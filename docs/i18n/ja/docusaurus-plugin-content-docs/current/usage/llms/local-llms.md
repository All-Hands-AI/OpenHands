# OllamaによるローカルLLM

:::warning
ローカルLLMを使用する場合、OpenHandsの機能が制限される可能性があります。
:::

Ollamaサーバーが動作していることを確認してください。
起動方法の詳細な手順については、[こちら](https://github.com/ollama/ollama)を参照してください。

このガイドでは、`ollama serve`でollamaを起動していることを前提としています。ollamaを異なる方法（例：docker内）で実行している場合、手順の修正が必要になる場合があります。WSLを使用している場合、ollamaのデフォルト設定ではdockerコンテナからのリクエストがブロックされることに注意してください。[こちら](#configuring-ollama-service-wsl-ja)を参照してください。

## モデルの取得

Ollamaのモデル名は[こちら](https://ollama.com/library)で確認できます。小さな例として、`codellama:7b`モデルを使用できます。より大きなモデルは一般的により良いパフォーマンスを示します。

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

## Dockerを使用したOpenHandsの実行

### OpenHandsの起動
Dockerを使用してOpenHandsを起動するには[こちら](../getting-started)の手順を使用してください。
ただし、`docker run`を実行する際に、以下の追加引数が必要です：

```bash
docker run # ...
    --add-host host.docker.internal:host-gateway \
    -e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    # ...
```

LLM_OLLAMA_BASE_URLはオプションです。設定すると、UIでインストール済みの利用可能なモデルを
表示するために使用されます。

### Webアプリケーションの設定

`openhands`を実行する際、OpenHandsのUIで設定メニューから以下の項目を設定する必要があります：
- モデルを"ollama/&lt;model-name&gt;"に設定
- ベースURLを`http://host.docker.internal:11434`に設定
- APIキーはオプションで、`ollama`などの任意の文字列を使用できます。

## 開発モードでのOpenHandsの実行

### ソースからのビルド

[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)の手順を使用してOpenHandsをビルドしてください。
`make setup-config`を実行して`config.toml`が存在することを確認してください。これにより新しいファイルが作成されます。`config.toml`に以下を入力してください：

```
[core]
workspace_base="./workspace"

[llm]
embedding_model="local"
ollama_base_url="http://localhost:11434"
```

完了です！これで`make run`でOpenHandsを起動できます。`http://localhost:3000/`に接続できるはずです。

### Webアプリケーションの設定

OpenHandsのUIで、左下の設定アイコンをクリックしてください。
次に、`モデル`フィールドに`ollama/codellama:7b`、または先ほど取得したモデル名を入力してください。
ドロップダウンリストに表示されない場合は、`詳細設定`を有効にして入力してください。注意：`ollama list`で表示されるモデル名に`ollama/`プレフィックスを付けた名前が必要です。

APIキーフィールドには、特定のキーは必要ないため、`ollama`または任意の値を入力してください。

ベースURLフィールドには、`http://localhost:11434`を入力してください。

これで準備完了です！

## ollamaサービスの設定（WSL） {#configuring-ollama-service-wsl-ja}

WSLでのollamaのデフォルト設定では、localhostのみを提供します。これは、dockerコンテナからアクセスできないことを意味します。例えば、OpenHandsでは動作しません。まず、ollamaが正しく動作しているかテストしましょう。

```bash
ollama list # インストール済みモデルのリストを取得
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例：curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#例：curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #タグは1つしかない場合はオプション
```

これが完了したら、dockerコンテナなどからの「外部」リクエストを許可するかテストします。

```bash
docker ps # 実行中のdockerコンテナのリストを取得、より正確なテストのためにOpenHandsのsandboxコンテナを選択
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例：docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## 問題の解決

では、これを動作させましょう。sudo権限で/etc/systemd/system/ollama.serviceを編集します。（パスはLinuxディストリビューションによって異なる場合があります）

```bash
sudo vi /etc/systemd/system/ollama.service
```

または

```bash
sudo nano /etc/systemd/system/ollama.service
```

[Service]ブロックに以下の行を追加します

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

次に、保存して設定をリロードし、サービスを再起動します。

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

最後に、コンテナからollamaにアクセスできることをテストします

```bash
ollama list # インストール済みモデルのリストを取得
docker ps # 実行中のdockerコンテナのリストを取得、より正確なテストのためにOpenHandsのsandboxコンテナを選択
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```

# LM StudioによるローカルLLM

LM Studioの設定手順：
1. LM Studioを開く
2. ローカルサーバータブに移動
3. "サーバーを起動"ボタンをクリック
4. ドロップダウンリストから使用したいモデルを選択

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

これで`http://localhost:3000/`に接続できるはずです。

開発環境では、`config.toml`ファイルで以下の設定を行うことができます：

```
[core]
workspace_base="./workspace"

[llm]
model="openai/lmstudio"
base_url="http://localhost:1234/v1"
custom_llm_provider="openai"
```

完了です！これでDockerなしで`make run`を使用してOpenHandsを起動できます。`http://localhost:3000/`に接続できるはずです。

# 注意

WSLの場合、cmdで以下のコマンドを実行してミラーネットワークモードを設定してください：

```
python -c  "print('[wsl2]\nnetworkingMode=mirrored',file=open(r'%UserProfile%\.wslconfig','w'))"
wsl --shutdown
```
