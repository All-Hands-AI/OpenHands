# 🚧 故障排除

:::tip
OpenHands 仅通过 WSL 支持 Windows。请确保在 WSL 终端中运行所有命令。
:::

### 无法通过本地 IP 访问 VS Code 标签页

**描述**

当通过非本地主机 URL（如 LAN IP 地址）访问 OpenHands 时，VS Code 标签页显示"禁止访问"错误，而 UI 的其他部分正常工作。

**解决方案**

这是因为 VS Code 运行在随机的高端口上，可能没有暴露或无法从其他机器访问。要解决此问题：

1. 使用 `SANDBOX_VSCODE_PORT` 环境变量为 VS Code 设置特定端口：
   ```bash
   docker run -it --rm \
       -e SANDBOX_VSCODE_PORT=41234 \
       -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:latest \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.openhands-state:/.openhands-state \
       -p 3000:3000 \
       -p 41234:41234 \
       --add-host host.docker.internal:host-gateway \
       --name openhands-app \
       docker.all-hands.dev/all-hands-ai/openhands:latest
   ```

2. 确保在 Docker 命令中使用 `-p 41234:41234` 暴露相同的端口。

3. 或者，您可以在 `config.toml` 文件中设置：
   ```toml
   [sandbox]
   vscode_port = 41234
   ```

### 启动 docker 客户端失败

**描述**

运行 OpenHands 时，出现以下错误：
```
Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.
```

**解决方案**

按顺序尝试以下方法：
* 确认系统上正在运行 `docker`。您应该能够在终端中成功运行 `docker ps`。
* 如果使用 Docker Desktop，确保启用了 `设置 > 高级 > 允许使用默认 Docker 套接字`。
* 根据您的配置，可能需要在 Docker Desktop 中启用 `设置 > 资源 > 网络 > 启用主机网络`。
* 重新安装 Docker Desktop。

### 权限错误

**描述**

在初始提示时，出现带有 `Permission Denied` 或 `PermissionError` 的错误。

**解决方案**

* 检查 `~/.openhands-state` 是否由 `root` 拥有。如果是，您可以：
  * 更改目录的所有权：`sudo chown <user>:<user> ~/.openhands-state`。
  * 或更新目录的权限：`sudo chmod 777 ~/.openhands-state`
  * 或者如果您不需要之前的数据，可以删除它。OpenHands 将重新创建它。您需要重新输入 LLM 设置。
* 如果挂载本地目录，确保您的 `WORKSPACE_BASE` 对运行 OpenHands 的用户有必要的权限。
