# カスタムサンドボックス

:::note
このガイドは、ランタイム用に独自のカスタムDockerイメージを使用したいユーザー向けです。例えば、
特定のツールやプログラミング言語があらかじめインストールされているものなどです。
:::

サンドボックスはエージェントがタスクを実行する場所です。コマンドをあなたのコンピュータで直接実行する
（これはリスクがあります）代わりに、エージェントはDockerコンテナ内でコマンドを実行します。

デフォルトのOpenHandsサンドボックス（[nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)から
`python-nodejs:python3.12-nodejs22`）にはpythonやNode.jsなどのパッケージがインストールされていますが、
他のソフトウェアをデフォルトでインストールする必要がある場合があります。

カスタマイズには2つの選択肢があります：

- 必要なソフトウェアがインストールされた既存のイメージを使用する。
- 独自のカスタムDockerイメージを作成する。

最初の選択肢を選ぶ場合は、「Dockerイメージの作成」セクションをスキップできます。

## Dockerイメージの作成

カスタムDockerイメージを作成するには、Debianベースである必要があります。

例えば、OpenHandsに`ruby`をインストールしたい場合、以下の内容で`Dockerfile`を作成できます：

```dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y ruby
```

または、Rubyに特化したベースイメージを使用することもできます：

```dockerfile
FROM ruby:latest
```

このファイルをフォルダに保存します。次に、ターミナルでそのフォルダに移動し、以下のコマンドを実行してDockerイメージ（例：custom-image）をビルドします：
```bash
docker build -t custom-image .
```

これにより、`custom-image`という名前の新しいイメージが作成され、Docker内で利用可能になります。

## Dockerコマンドの使用

[dockerコマンド](/modules/usage/installation#start-the-app)を使用してOpenHandsを実行する場合、
`-e SANDBOX_RUNTIME_CONTAINER_IMAGE=...`を`-e SANDBOX_BASE_CONTAINER_IMAGE=<カスタムイメージ名>`に置き換えます：

```commandline
docker run -it --rm --pull=always \
    -e SANDBOX_BASE_CONTAINER_IMAGE=custom-image \
    ...
```

## 開発ワークフローの使用

### セットアップ

まず、[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)の指示に従ってOpenHandsを実行できることを確認してください。

### ベースサンドボックスイメージの指定

OpenHandsディレクトリ内の`config.toml`ファイルで、`base_container_image`を使用したいイメージに設定します。
これは既に取得したイメージか、ビルドしたイメージのいずれかです：

```bash
[core]
...
[sandbox]
base_container_image="custom-image"
```

### 追加の設定オプション

`config.toml`ファイルでは、サンドボックスをカスタマイズするための他のオプションもサポートしています：

```toml
[core]
# ランタイムがビルドされるときに追加の依存関係をインストール
# 有効なシェルコマンドを含めることができます
# これらのコマンドでPythonインタプリタのパスが必要な場合は、$OH_INTERPRETER_PATH変数を使用できます
runtime_extra_deps = """
pip install numpy pandas
apt-get update && apt-get install -y ffmpeg
"""

# ランタイム用の環境変数を設定
# ランタイム時に利用可能にする必要がある設定に役立ちます
runtime_startup_env_vars = { DATABASE_URL = "postgresql://user:pass@localhost/db" }

# マルチアーキテクチャビルド用のプラットフォームを指定（例：「linux/amd64」または「linux/arm64」）
platform = "linux/amd64"
```

### 実行

トップレベルディレクトリで```make run```を実行してOpenHandsを起動します。
