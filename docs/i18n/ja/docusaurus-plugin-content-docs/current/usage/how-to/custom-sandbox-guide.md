# カスタムサンドボックス

サンドボックスは、エージェントがタスクを実行する場所です。コンピュータ上で直接コマンドを実行する（これはリスクがある可能性があります）代わりに、エージェントはDockerコンテナ内でそれらを実行します。

デフォルトのOpenHandsサンドボックス（[nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)の`python-nodejs:python3.12-nodejs22`）にはPythonやNode.jsなどのパッケージがインストールされていますが、デフォルトでインストールする必要のある他のソフトウェアがある場合があります。

カスタマイズには2つのオプションがあります:

- 必要なソフトウェアがインストールされている既存のイメージを使用する。
- 独自のカスタムDockerイメージを作成する。

最初のオプションを選択した場合は、`Dockerイメージの作成`セクションをスキップできます。

## Dockerイメージの作成

カスタムDockerイメージを作成するには、Debianベースである必要があります。

たとえば、OpenHandsに`ruby`をインストールしたい場合は、次の内容で`Dockerfile`を作成できます:

```dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y ruby
```

または、Ruby固有のベースイメージを使用することもできます:

```dockerfile
FROM ruby:latest
```

このファイルをフォルダに保存します。次に、ターミナルでフォルダに移動し、次のコマンドを実行して、Dockerイメージ（たとえば、custom-imageという名前）をビルドします:

```bash
docker build -t custom-image .
```

これにより、`custom-image`という新しいイメージが作成され、Dockerで利用できるようになります。

## Dockerコマンドの使用

[dockerコマンド](/modules/usage/installation#start-the-app)を使用してOpenHandsを実行する場合は、`-e SANDBOX_RUNTIME_CONTAINER_IMAGE=...`を`-e SANDBOX_BASE_CONTAINER_IMAGE=<カスタムイメージ名>`に置き換えます:

```commandline
docker run -it --rm --pull=always \
    -e SANDBOX_BASE_CONTAINER_IMAGE=custom-image \
    ...
```

## 開発ワークフローの使用

### セットアップ

まず、[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)の手順に従って、OpenHandsを実行できることを確認してください。

### ベースサンドボックスイメージの指定

OpenHandsディレクトリ内の`config.toml`ファイルで、`base_container_image`を使用するイメージに設定します。これは、すでにプルしたイメージまたは構築したイメージにすることができます:

```bash
[core]
...
[sandbox]
base_container_image="custom-image"
```

### その他の設定オプション

`config.toml`ファイルは、サンドボックスをカスタマイズするためのいくつかの他のオプションをサポートしています:

```toml
[core]
# ランタイムのビルド時に追加の依存関係をインストールする
# 有効なシェルコマンドを含めることができる
# これらのコマンドのいずれかでPythonインタープリターへのパスが必要な場合は、$OH_INTERPRETER_PATH変数を使用できる
runtime_extra_deps = """
pip install numpy pandas
apt-get update && apt-get install -y ffmpeg
"""

# ランタイムの環境変数を設定する
# ランタイムで使用可能である必要がある設定に役立つ
runtime_startup_env_vars = { DATABASE_URL = "postgresql://user:pass@localhost/db" }

# マルチアーキテクチャビルドのプラットフォームを指定する（例: "linux/amd64"または"linux/arm64"）
platform = "linux/amd64"
```

### 実行

トップレベルのディレクトリで```make run```を実行して、OpenHandsを実行します。
