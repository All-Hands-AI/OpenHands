以下是翻译后的内容:

# 无头模式

你可以使用单个命令运行 OpenHands,而无需启动 Web 应用程序。
这使得使用 OpenHands 编写脚本和自动化任务变得很容易。

这与[CLI 模式](cli-mode)不同,后者是交互式的,更适合主动开发。

## 使用 Python

要在 Python 中以无头模式运行 OpenHands,
[请按照开发设置说明](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md),
然后运行:

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

你需要确保通过环境变量
[或 `config.toml` 文件](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)
设置你的模型、API 密钥和其他设置。

## 使用 Docker

1. 将 `WORKSPACE_BASE` 设置为你希望 OpenHands 编辑的目录:

```bash
WORKSPACE_BASE=$(pwd)/workspace
```

2. 将 `LLM_MODEL` 设置为你要使用的模型:

```bash
LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"

```

3. 将 `LLM_API_KEY` 设置为你的 API 密钥:

```bash
LLM_API_KEY="sk_test_12345"
```

4. 运行以下 Docker 命令:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.19-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.19 \
    python -m openhands.core.main -t "write a bash script that prints hi" --no-auto-continue
```
