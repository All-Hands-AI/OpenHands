# 使用 Ollama 的本地 LLM

:::warning
使用本地 LLM 时，OpenHands 可能会有功能限制。
:::

确保你已经启动并运行了 Ollama 服务器。
有关详细的启动说明，请参考[此处](https://github.com/ollama/ollama)。

本指南假设你已经使用 `ollama serve` 启动了 ollama。如果你以不同的方式运行 ollama（例如在 docker 内），则可能需要修改说明。请注意，如果你正在运行 WSL，默认的 ollama 配置会阻止来自 docker 容器的请求。请参阅[此处](#configuring-ollama-service-wsl-zh)。

## 拉取模型

Ollama 模型名称可以在[此处](https://ollama.com/library)找到。对于一个小示例，你可以使用
`codellama:7b` 模型。更大的模型通常会有更好的表现。

```bash
ollama pull codellama:7b
```

你可以像这样检查已下载的模型：

```bash
~$ ollama list
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## 使用 Docker 运行 OpenHands

### 启动 OpenHands
使用[此处](../getting-started)的说明使用 Docker 启动 OpenHands。
但在运行 `docker run` 时，你需要添加一些额外的参数：

```bash
docker run # ...
    --add-host host.docker.internal:host-gateway \
    -e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    # ...
```

LLM_OLLAMA_BASE_URL 是可选的。如果设置了它，它将用于在 UI 中显示
可用的已安装模型。


### 配置 Web 应用程序

在运行 `openhands` 时，你需要在 OpenHands UI 的设置中设置以下内容：
- 模型设置为 "ollama/&lt;model-name&gt;"
- 基础 URL 设置为 `http://host.docker.internal:11434`
- API 密钥是可选的，你可以使用任何字符串，例如 `ollama`。


## 在开发模式下运行 OpenHands

### 从源代码构建

使用 [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) 中的说明构建 OpenHands。
通过运行 `make setup-config` 确保 `config.toml` 存在，它将为你创建一个。在 `config.toml` 中，输入以下内容：

```
[core]
workspace_base="./workspace"

[llm]
embedding_model="local"
ollama_base_url="http://localhost:11434"

```

完成！现在你可以通过 `make run` 启动 OpenHands。你现在应该能够连接到 `http://localhost:3000/`

### 配置 Web 应用程序

在 OpenHands UI 中，点击左下角的设置齿轮。
然后在 `Model` 输入框中，输入 `ollama/codellama:7b`，或者你之前拉取的模型名称。
如果它没有出现在下拉列表中，启用 `Advanced Settings` 并输入它。请注意：你需要 `ollama list` 列出的模型名称，带有 `ollama/` 前缀。

在 API Key 字段中，输入 `ollama` 或任何值，因为你不需要特定的密钥。

在 Base URL 字段中，输入 `http://localhost:11434`。

现在你已经准备好了！

## 配置 ollama 服务（WSL） {#configuring-ollama-service-wsl-zh}

WSL 中 ollama 的默认配置只服务于 localhost。这意味着你无法从 docker 容器中访问它。例如，它不能与 OpenHands 一起工作。首先让我们测试 ollama 是否正确运行。

```bash
ollama list # 获取已安装模型的列表
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例如 curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#例如 curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #如果只有一个，标签是可选的
```

完成后，测试它是否允许"外部"请求，例如来自 docker 容器内部的请求。

```bash
docker ps # 获取正在运行的 docker 容器列表，为了最准确的测试，选择 OpenHands 沙盒容器。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#例如 docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## 修复它

现在让我们让它工作。使用 sudo 权限编辑 /etc/systemd/system/ollama.service。（路径可能因 Linux 发行版而异）

```bash
sudo vi /etc/systemd/system/ollama.service
```

或

```bash
sudo nano /etc/systemd/system/ollama.service
```

在 [Service] 括号中添加这些行

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

然后保存，重新加载配置并重启服务。

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

最后测试 ollama 是否可以从容器内访问

```bash
ollama list # 获取已安装模型的列表
docker ps # 获取正在运行的 docker 容器列表，为了最准确的测试，选择 OpenHands 沙盒容器。
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```


# 使用 LM Studio 的本地 LLM

设置 LM Studio 的步骤：
1. 打开 LM Studio
2. 转到 Local Server 选项卡。
3. 点击 "Start Server" 按钮。
4. 从下拉列表中选择要使用的模型。


设置以下配置：
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

你现在应该能够连接到 `http://localhost:3000/`

在开发环境中，你可以在 `config.toml` 文件中设置以下配置：

```
[core]
workspace_base="./workspace"

[llm]
model="openai/lmstudio"
base_url="http://localhost:1234/v1"
custom_llm_provider="openai"
```

完成！现在你可以通过 `make run` 启动 OpenHands，无需 Docker。你现在应该能够连接到 `http://localhost:3000/`

# 注意

对于 WSL，在 cmd 中运行以下命令以将网络模式设置为镜像：

```
python -c  "print('[wsl2]\nnetworkingMode=mirrored',file=open(r'%UserProfile%\.wslconfig','w'))"
wsl --shutdown
```
