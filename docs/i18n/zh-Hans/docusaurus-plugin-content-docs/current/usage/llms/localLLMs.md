# 使用 Ollama 的本地 LLM

确保您的 Ollama 服务器已启动运行。有关详细的启动说明，请参阅[此处](https://github.com/ollama/ollama)

本指南假定您已通过 `ollama serve` 启动 ollama。如果您以其他方式运行 ollama（例如在 docker 内），说明可能需要进行修改。请注意，如果您在运行 WSL，默认的 ollama 配置会阻止来自 docker 容器的请求。请参阅[此处](#configuring-ollama-service-zh-Hans)。

## 拉取模型

Ollama 模型名称可以在[这里](https://ollama.com/library)找到。一个小例子，您可以使用
`codellama:7b` 模型。较大的模型通常表现更好。

```bash
ollama pull codellama:7b
```

您可以这样检查已下载的模型：

```bash
~$ ollama list
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## 启动 OpenHands

### Docker

使用[此处](../intro)的说明通过 Docker 启动 OpenHands。
但是在运行 `docker run` 时，您需要添加一些额外的参数：

```bash
--add-host host.docker.internal:host-gateway \
-e LLM_API_KEY="ollama" \
-e LLM_BASE_URL="http://host.docker.internal:11434" \
```

例如：

```bash
# 您希望 OpenHands 修改的目录。必须是绝对路径！
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

现在您应该可以连接到 `http://localhost:3000/`

### 从源代码构建

使用[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)中的说明构建 OpenHands。
通过运行 `make setup-config` 确保 `config.toml` 存在，这将为您创建一个。在 `config.toml` 中，输入以下内容：

```
LLM_MODEL="ollama/codellama:7b"
LLM_API_KEY="ollama"
LLM_EMBEDDING_MODEL="local"
LLM_BASE_URL="http://localhost:11434"
WORKSPACE_BASE="./workspace"
WORKSPACE_DIR="$(pwd)/workspace"
```

如有需要，可以替换您选择的 `LLM_MODEL`。

完成！现在您可以通过 `make run` 启动 OpenHands 而无需 Docker。现在您应该可以连接到 `http://localhost:3000/`

## 选择您的模型

在 OpenHands UI 中，点击左下角的设置齿轮。
然后在 `Model` 输入中，输入 `ollama/codellama:7b`，或者您之前拉取的模型名称。
如果它没有出现在下拉列表中，也没关系，只需输入即可。完成后点击保存。

现在您已经准备好了！

## 配置 ollama 服务（WSL）{#configuring-ollama-service-zh-Hans}

WSL 中 ollama 的默认配置仅为 localhost 提供服务。这意味着您无法从 docker 容器中访问它。比如，它不会与 OpenHands 一起工作。首先让我们测试 ollama 是否正常运行。

```bash
ollama list # 获取已安装模型列表
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例如，curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#例如，curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'  # 如果只有一个模型，标签是可选的
```

完成后，测试它是否允许“外部”请求，比如那些来自 docker 容器内的请求。

```bash
docker ps # 获取正在运行的 docker 容器列表，最准确的测试选择 OpenHands sandbox 容器。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例如，docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## 修复它

现在让我们使其工作。使用 sudo 权限编辑 /etc/systemd/system/ollama.service。 （路径可能因 linux 版本而异）

```bash
sudo vi /etc/systemd/system/ollama.service
```

或者

```bash
sudo nano /etc/systemd/system/ollama.service
```

在 [Service] 括号内添加以下行

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

然后保存，重新加载配置并重新启动服务。

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

最后测试 ollama 是否可以从容器内访问

```bash
ollama list # 获取已安装模型列表
docker ps # 获取正在运行的 docker 容器列表，最准确的测试选择 OpenHands sandbox 容器。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```
