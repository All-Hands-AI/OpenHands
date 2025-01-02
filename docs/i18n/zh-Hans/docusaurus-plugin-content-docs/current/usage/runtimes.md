# 运行时配置

运行时是 OpenHands 代理可以编辑文件和运行命令的环境。

默认情况下，OpenHands 使用基于 Docker 的运行时，在您的本地计算机上运行。这意味着您只需要为使用的 LLM 付费，并且您的代码只会发送到 LLM。

我们还支持"远程"运行时，通常由第三方管理。它们可以使设置更简单、更具可扩展性，特别是当您并行运行多个 OpenHands 对话时（例如进行评估）。

## Docker 运行时
这是启动 OpenHands 时使用的默认运行时。您可能会注意到传递给 `docker run` 的一些标志使这成为可能：

```
docker run # ...
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.17-nikolaik \
    -v /var/run/docker.sock:/var/run/docker.sock \
    # ...
```

来自 nikolaik 的 `SANDBOX_RUNTIME_CONTAINER_IMAGE` 是一个预构建的运行时镜像，其中包含我们的运行时服务器，以及一些用于 Python 和 NodeJS 的基本实用程序。您也可以[构建自己的运行时镜像](how-to/custom-sandbox-guide)。

### 连接到您的文件系统
这里一个有用的功能是能够连接到您的本地文件系统。

要将文件系统挂载到运行时，首先设置 WORKSPACE_BASE：
```bash
export WORKSPACE_BASE=/path/to/your/code

# Linux 和 Mac 示例
# export WORKSPACE_BASE=$HOME/OpenHands
# 将 $WORKSPACE_BASE 设置为 /home/<username>/OpenHands
#
# Windows 上的 WSL 示例
# export WORKSPACE_BASE=/mnt/c/dev/OpenHands
# 将 $WORKSPACE_BASE 设置为 C:\dev\OpenHands
```

然后将以下选项添加到 `docker run` 命令中：

```bash
docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    # ...
```

请小心！没有任何措施可以阻止 OpenHands 代理删除或修改挂载到其工作区的任何文件。

此设置可能会导致一些文件权限问题（因此有 `SANDBOX_USER_ID` 变量），但似乎在大多数系统上都能很好地工作。

## All Hands 运行时
All Hands 运行时目前处于测试阶段。您可以通过加入 Slack 上的 #remote-runtime-limited-beta 频道来请求访问权限（[请参阅自述文件](https://github.com/All-Hands-AI/OpenHands?tab=readme-ov-file#-join-our-community)以获取邀请）。

要使用 All Hands 运行时，请在启动 OpenHands 时设置以下环境变量：

```bash
docker run # ...
    -e RUNTIME=remote \
    -e SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.app.all-hands.dev" \
    -e SANDBOX_API_KEY="your-all-hands-api-key" \
    -e SANDBOX_KEEP_RUNTIME_ALIVE="true" \
    # ...
```

## Modal 运行时
我们在 [Modal](https://modal.com/) 的合作伙伴也为 OpenHands 提供了一个运行时。

要使用 Modal 运行时，请创建一个帐户，然后[创建一个 API 密钥](https://modal.com/settings)。

然后，您需要在启动 OpenHands 时设置以下环境变量：
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="your-id" \
    -e MODAL_API_TOKEN_SECRET="your-secret" \
```
