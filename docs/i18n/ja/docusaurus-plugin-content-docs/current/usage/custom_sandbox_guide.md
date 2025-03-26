# 💿 カスタム Docker サポートを作成する方法

デフォルトの OpenHands サンドボックスは、最小限の ubuntu 構成で提供されています。ユースケースによっては、デフォルトでインストールされているソフトウェアが必要になる場合があります。この記事では、カスタム docker イメージを使用してこれを実現する方法について説明します。

## セットアップ

[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) のドキュメントに従って、OpenHands を使用できるようにしてください。

## カスタム Docker イメージの作成

次に、debian/ubuntu ベースのカスタム docker イメージを作成する必要があります。たとえば、OpenHands で "node" バイナリにアクセスできるようにしたい場合は、次のような Dockerfile を使用します:

```bash
# 最新の ubuntu イメージから開始
FROM ubuntu:latest

# 必要なアップデートを実行
RUN apt-get update && apt-get install

# nodejs をインストール
RUN apt-get install -y nodejs
```

次に、選択した名前でカスタム docker イメージをビルドします。たとえば、"custom_image" とします。そのためには、ディレクトリを作成し、"Dockerfile" という名前のファイルをその中に配置し、ディレクトリ内でこのコマンドを実行します:

```bash
docker build -t custom_image .
```

これにより、```custom_image``` という名前の新しいイメージが作成され、Docker Engine で利用できるようになります。

> 注: ここで説明する設定では、OpenHands はサンドボックス内で "openhands" ユーザーとして動作するため、Dockerfile 経由でインストールされたパッケージは、root だけでなくシステム上のすべてのユーザーが利用できるようになります。
>
> 上記の apt-get によるインストールでは、すべてのユーザー向けに nodejs がインストールされます。

## config.toml ファイルでカスタムイメージを指定

OpenHands の設定は、トップレベルの ```config.toml``` ファイルを介して行われます。
OpenHands ディレクトリに ```config.toml``` ファイルを作成し、次の内容を入力します:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
[sandbox]
base_container_image="custom_image"
```

> ```base_container_image``` が前述のカスタムイメージ名に設定されていることを確認してください。

## 実行

ルートディレクトリで ```make run``` を実行して OpenHands を起動します。

```localhost:3001``` に移動し、目的の依存関係が利用可能かどうかを確認します。

上記の例の場合、コンソールで ```node -v``` コマンドを実行すると ```v18.19.1``` が出力されます。

おめでとうございます！

## 技術的な説明

カスタムイメージが初めて使用される場合、イメージが見つからないため、ビルドされます (その後の実行では、ビルドされたイメージが見つかり、返されます)。

カスタムイメージは [_build_sandbox_image()](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/image_agnostic_util.py#L29) でビルドされます。これは、カスタムイメージをベースとして使用して docker ファイルを作成し、次のように OpenHands の環境を設定します:

```python
dockerfile_content = (
        f'FROM {base_image}\n'
        'RUN apt update && apt install -y openssh-server wget sudo\n'
        'RUN mkdir -p -m0755 /var/run/sshd\n'
        'RUN mkdir -p /openhands && mkdir -p /openhands/logs && chmod 777 /openhands/logs\n'
        'RUN wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"\n'
        'RUN bash Miniforge3-$(uname)-$(uname -m).sh -b -p /openhands/miniforge3\n'
        'RUN bash -c ". /openhands/miniforge3/etc/profile.d/conda.sh && conda config --set changeps1 False && conda config --append channels conda-forge"\n'
        'RUN echo "export PATH=/openhands/miniforge3/bin:$PATH" >> ~/.bashrc\n'
        'RUN echo "export PATH=/openhands/miniforge3/bin:$PATH" >> /openhands/bash.bashrc\n'
    ).strip()
```

> 注: イメージ名は [_get_new_image_name()](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/docker/image_agnostic_util.py#L63) で変更され、この変更された名前が後続の実行時に検索されます。

## トラブルシューティング / エラー

### エラー: ```useradd: UID 1000 は一意ではありません```
このエラーがコンソール出力に表示される場合、OpenHands がサンドボックス内に UID 1000 で openhands ユーザーを作成しようとしていますが、この UID は (何らかの理由で) イメージ内ですでに使用されているためです。この問題を解決するには、config.toml ファイルの user_id フィールドの値を別の値に変更します:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
[sandbox]
base_container_image="custom_image"
user_id="1001"
```

### ポート使用エラー

ポートが使用中または利用不可であることを示すエラーメッセージが表示される場合は、実行中のすべての docker コンテナを削除してみてください (`docker ps` を実行し、関連するコンテナに対して `docker rm` を実行します)。その後、```make run``` を再実行します。
