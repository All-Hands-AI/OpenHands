# Docker 运行时

这是启动 OpenHands 时默认使用的运行时。

## 镜像
来自 nikolaik 的 `SANDBOX_RUNTIME_CONTAINER_IMAGE` 是一个预构建的运行时镜像，
其中包含我们的运行时服务器，以及一些 Python 和 NodeJS 的基本工具。
您也可以[构建自己的运行时镜像](../how-to/custom-sandbox-guide)。

## 连接到您的文件系统
一个有用的功能是能够连接到您的本地文件系统。要将您的文件系统挂载到运行时中：

### 使用 SANDBOX_VOLUMES

挂载本地文件系统最简单的方法是使用 `SANDBOX_VOLUMES` 环境变量：

```bash
docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=/path/to/your/code:/workspace:rw \
    # ...
```

`SANDBOX_VOLUMES` 格式为：`host_path:container_path[:mode]`

- `host_path`：您想要挂载的主机路径
- `container_path`：容器内挂载主机路径的位置
  - 对于您希望代理修改的文件，请使用 `/workspace`。代理默认在 `/workspace` 中工作。
  - 对于只读参考材料或大型数据集，请使用不同的路径（例如 `/data`）
- `mode`：可选的挂载模式，可以是 `rw`（读写，默认）或 `ro`（只读）

您也可以通过逗号（`,`）分隔来指定多个挂载点：

```bash
export SANDBOX_VOLUMES=/path1:/workspace/path1,/path2:/workspace/path2:ro
```

示例：

```bash
# Linux 和 Mac 示例 - 可写工作区
export SANDBOX_VOLUMES=$HOME/OpenHands:/workspace:rw

# Windows 上的 WSL 示例 - 可写工作区
export SANDBOX_VOLUMES=/mnt/c/dev/OpenHands:/workspace:rw

# 只读参考代码示例
export SANDBOX_VOLUMES=/path/to/reference/code:/data:ro

# 多挂载点示例 - 可写工作区和只读参考数据
export SANDBOX_VOLUMES=$HOME/projects:/workspace:rw,/path/to/large/dataset:/data:ro
```

> **注意：** 使用多个挂载点时，第一个挂载点被视为主要工作区，并将用于向后兼容那些期望单一工作区的工具。

> **重要：** 代理默认在 `/workspace` 中工作。如果您希望代理修改您本地目录中的文件，您应该将该目录挂载到 `/workspace`。如果您有希望代理访问但不修改的只读数据，请将其挂载到不同的路径（如 `/data`），并明确指示代理在那里查找。

### 使用 WORKSPACE_* 变量（已弃用）

> **注意：** 此方法已弃用，将在未来版本中移除。请改用 `SANDBOX_VOLUMES`。

1. 设置 `WORKSPACE_BASE`：

    ```bash
    export WORKSPACE_BASE=/path/to/your/code
    ```

2. 在 `docker run` 命令中添加以下选项：

    ```bash
    docker run # ...
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
        -v $WORKSPACE_BASE:/opt/workspace_base \
        # ...
    ```

请小心！没有任何措施可以阻止 OpenHands 代理删除或修改挂载到其工作区的任何文件。

将 `-e SANDBOX_USER_ID=$(id -u)` 传递给 Docker 命令是为了确保沙箱用户与主机用户的权限匹配。这可以防止代理在挂载的工作区中创建 root 所有的文件。

## 强化的 Docker 安装

在安全性是优先考虑因素的环境中部署 OpenHands 时，您应该考虑实施强化的 Docker 配置。本节提供了超出默认配置的建议，以保护您的 OpenHands Docker 部署。

### 安全考虑因素

README 中的默认 Docker 配置旨在方便本地开发机器使用。如果您在公共网络（例如机场 WiFi）上运行，应该实施额外的安全措施。

### 网络绑定安全

默认情况下，OpenHands 绑定到所有网络接口（`0.0.0.0`），这可能会将您的实例暴露给主机连接的所有网络。对于更安全的设置：

1. **限制网络绑定**：使用 `runtime_binding_address` 配置来限制 OpenHands 监听的网络接口：

   ```bash
   docker run # ...
       -e SANDBOX_RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       # ...
   ```

   此配置确保 OpenHands 只在回环接口（`127.0.0.1`）上监听，使其只能从本地机器访问。

2. **安全端口绑定**：修改 `-p` 标志，使其只绑定到 localhost 而不是所有接口：

   ```bash
   docker run # ... \
       -p 127.0.0.1:3000:3000 \
   ```

   这确保 OpenHands 网页界面只能从本地机器访问，而不能从网络上的其他机器访问。

### 网络隔离

使用 Docker 的网络功能来隔离 OpenHands：

```bash
# 创建一个隔离的网络
docker network create openhands-network

# 在隔离的网络中运行 OpenHands
docker run # ... \
    --network openhands-network \
```
