以下是翻译后的内容:

# 针对 Windows 上 WSL 用户的注意事项

OpenHands 仅通过 [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) 支持 Windows。
请确保在您的 WSL 终端内运行所有命令。

## 故障排除

### 建议: 不要以 root 用户身份运行

出于安全原因,强烈建议不要以 root 用户身份运行 OpenHands,而是以具有非零 UID 的用户身份运行。

参考:

* [为什么以 root 身份登录不好](https://askubuntu.com/questions/16178/why-is-it-bad-to-log-in-as-root)
* [在 WSL 中设置默认用户](https://www.tenforums.com/tutorials/128152-set-default-user-windows-subsystem-linux-distro-windows-10-a.html#option2)
关于第二个参考的提示:对于 Ubuntu 用户,命令实际上可能是 "ubuntupreview" 而不是 "ubuntu"。

---
### 错误: 在此 WSL 2 发行版中找不到 'docker'。

如果您正在使用 Docker Desktop,请确保在从 WSL 内部调用任何 docker 命令之前启动它。
Docker 还需要激活 WSL 集成选项。

---
### Poetry 安装

* 如果您在构建过程中安装 Poetry 后仍然面临运行 Poetry 的问题,您可能需要将其二进制路径添加到环境中:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

* 如果 make build 在如下错误上停止:

```sh
ModuleNotFoundError: no module named <module-name>
```

这可能是 Poetry 缓存的问题。
尝试依次运行这两个命令:

```sh
rm -r ~/.cache/pypoetry
make build
```

---
### NoneType 对象没有属性 'request'

如果您在执行 `make run` 时遇到与网络相关的问题,例如 `NoneType 对象没有属性 'request'`,您可能需要配置 WSL2 网络设置。请按照以下步骤操作:

* 在 Windows 主机上打开或创建位于 `C:\Users\%username%\.wslconfig` 的 `.wslconfig` 文件。
* 将以下配置添加到 `.wslconfig` 文件中:

```sh
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

* 保存 `.wslconfig` 文件。
* 通过退出任何正在运行的 WSL2 实例并在命令提示符或终端中执行 `wsl --shutdown` 命令来完全重启 WSL2。
* 重新启动 WSL 后,再次尝试执行 `make run`。
网络问题应该得到解决。
