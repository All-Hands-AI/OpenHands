# Windows 和 WSL 用户须知

OpenDevin 仅支持通过 [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) 在 Windows 上运行。
请确保在 WSL 终端内运行所有命令。

## 故障排除

### 错误：在此 WSL 2 发行版中找不到 'docker'。

如果您使用的是 Docker Desktop，请确保在 WSL 内部调用任何 docker 命令之前启动它。
Docker 还需要启用 WSL 集成选项。

### 建议：不要以 root 用户身份运行

出于安全原因，非常建议不要以 root 用户身份运行 OpenDevin，而是使用 UID 非零的用户身份运行。
此外，当以 root 身份运行时，不支持持久化沙箱，并且在启动 OpenDevin 时可能会出现相应消息。

参考资料：

* [为什么以 root 登录是不好的](https://askubuntu.com/questions/16178/why-is-it-bad-to-log-in-as-root)
* [在 WSL 中设置默认用户](https://www.tenforums.com/tutorials/128152-set-default-user-windows-subsystem-linux-distro-windows-10-a.html#option2)
关于第二个参考资料的小提示：对于 Ubuntu 用户，该命令实际上可能是 "ubuntupreview" 而不是 "ubuntu"。

### 创建 opendevin 用户失败

如果您在设置过程中遇到以下错误：

```sh
Exception: Failed to create opendevin user in sandbox: 'useradd: UID 0 is not unique'
```

您可以通过运行以下命令解决：

```sh
export SANDBOX_USER_ID=1000
```

### Poetry 安装

* 如果在构建过程中安装 Poetry 后仍然面临运行 Poetry 的问题，您可能需要将其二进制路径添加到您的环境变量：

```sh
export PATH="$HOME/.local/bin:$PATH"
```

* 如果 make build 停止并出现如下错误：

```sh
ModuleNotFoundError: no module named <module-name>
```

这可能是 Poetry 缓存的问题。
尝试运行以下两个命令：

```sh
rm -r ~/.cache/pypoetry
make build
```

### NoneType 对象没有属性 'request'

如果您在执行 `make run` 时遇到与网络相关的问题，例如 `NoneType object has no attribute 'request'`，您可能需要配置您的 WSL2 网络设置。请按照以下步骤操作：

* 打开或创建位于 Windows 主机机器上的 `C:\Users\%username%\.wslconfig` 文件。
* 向 `.wslconfig` 文件添加以下配置：

```sh
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

* 保存 `.wslconfig` 文件。
* 通过退出所有正在运行的 WSL2 实例并在命令提示符或终端中执行 `wsl --shutdown` 命令，完全重启 WSL2。
* 重新启动 WSL 后，尝试再次执行 `make run`。
   网络问题应该已经解决。
