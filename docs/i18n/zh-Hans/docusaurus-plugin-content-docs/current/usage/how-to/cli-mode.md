# CLI 模式

OpenHands 可以在交互式 CLI 模式下运行，允许用户通过命令行启动交互式会话。

这种模式与[无头模式](headless-mode)不同，后者是非交互式的，更适合脚本编写。

## 使用 Python

通过命令行启动交互式 OpenHands 会话：

1. 确保您已按照[开发环境设置说明](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)进行操作。
2. 运行以下命令：

```bash
poetry run python -m openhands.core.cli
```

此命令将启动一个交互式会话，您可以在其中输入任务并接收来自 OpenHands 的响应。

您需要确保通过环境变量[或 `config.toml` 文件](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)设置您的模型、API 密钥和其他设置。

## 使用 Docker

要使用 Docker 在 CLI 模式下运行 OpenHands：

1. 在终端中设置以下环境变量：

- `SANDBOX_VOLUMES` 指定您希望 OpenHands 访问的目录（例如：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw`）。
  - 代理默认在 `/workspace` 中工作，因此如果您希望代理修改文件，请将您的项目目录挂载到那里。
  - 对于只读数据，使用不同的挂载路径（例如：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw,/path/to/large/dataset:/data:ro`）。
- `LLM_MODEL` 设置要使用的模型（例如：`export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`）。
- `LLM_API_KEY` 设置 API 密钥（例如：`export LLM_API_KEY="sk_test_12345"`）。

2. 运行以下 Docker 命令：

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.39 \
    python -m openhands.core.cli
```

此命令将在 Docker 中启动一个交互式会话，您可以在其中输入任务并接收来自 OpenHands 的响应。

传递给 Docker 命令的 `-e SANDBOX_USER_ID=$(id -u)` 确保沙箱用户与主机用户的权限匹配。这可以防止代理在挂载的工作区中创建 root 拥有的文件。
