# 无头模式

您可以使用单个命令运行OpenHands，而无需启动Web应用程序。
这使得使用OpenHands编写脚本和自动化任务变得简单。

这与[CLI模式](cli-mode)不同，CLI模式是交互式的，更适合主动开发。

## 使用Python

要使用Python在无头模式下运行OpenHands：
1. 确保您已按照[开发设置说明](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)进行操作。
2. 运行以下命令：
```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

您需要确保通过环境变量或[`config.toml`文件](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)设置您的模型、API密钥和其他设置。

## 使用Docker

要使用Docker在无头模式下运行OpenHands：

1. 在终端中设置以下环境变量：

- `SANDBOX_VOLUMES`指定您希望OpenHands访问的目录（例如：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw`）。
  - 代理默认在`/workspace`中工作，所以如果您希望代理修改文件，请将您的项目目录挂载到那里。
  - 对于只读数据，使用不同的挂载路径（例如：`export SANDBOX_VOLUMES=$(pwd)/workspace:/workspace:rw,/path/to/large/dataset:/data:ro`）。
- `LLM_MODEL`设置为要使用的模型（例如：`export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`）。
- `LLM_API_KEY`设置为API密钥（例如：`export LLM_API_KEY="sk_test_12345"`）。

2. 运行以下Docker命令：

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.39-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=$SANDBOX_VOLUMES \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.39 \
    python -m openhands.core.main -t "write a bash script that prints hi"
```

传递给Docker命令的`-e SANDBOX_USER_ID=$(id -u)`确保沙箱用户与主机用户的权限匹配。这可以防止代理在挂载的工作区中创建root所有的文件。

## 高级无头模式配置

要查看无头模式的所有可用配置选项，请使用`--help`标志运行Python命令。

### 额外日志

要让无头模式记录所有代理操作，在终端中运行：`export LOG_ALL_EVENTS=true`
