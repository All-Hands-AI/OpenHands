# Daytona 运行时

您可以使用 [Daytona](https://www.daytona.io/) 作为运行时提供商：

## 步骤 1：获取您的 Daytona API 密钥
1. 访问 [Daytona 控制面板](https://app.daytona.io/dashboard/keys)。
2. 点击 **"Create Key"**。
3. 输入密钥名称并确认创建。
4. 密钥生成后，复制它。

## 步骤 2：将您的 API 密钥设置为环境变量
在终端中运行以下命令，将 `<your-api-key>` 替换为您复制的实际密钥：
```bash
export DAYTONA_API_KEY="<your-api-key>"
```

此步骤确保 OpenHands 在运行时可以与 Daytona 平台进行身份验证。

## 步骤 3：使用 Docker 在本地运行 OpenHands
要在您的机器上启动最新版本的 OpenHands，在终端中执行以下命令：
```bash
bash -i <(curl -sL https://get.daytona.io/openhands)
```

### 此命令的作用：
- 下载最新的 OpenHands 发布脚本。
- 在交互式 Bash 会话中运行脚本。
- 自动使用 Docker 拉取并运行 OpenHands 容器。

执行后，OpenHands 应该在本地运行并准备使用。

有关更多详细信息和手动初始化，请查看完整的 [README.md](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/impl/daytona/README.md)
