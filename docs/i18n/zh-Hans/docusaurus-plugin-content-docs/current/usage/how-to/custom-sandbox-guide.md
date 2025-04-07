# 自定义沙箱

沙箱是代理执行任务的地方。代理不是直接在你的计算机上运行命令（这可能有风险），而是在 Docker 容器内运行。

默认的 OpenHands 沙箱（`python-nodejs:python3.12-nodejs22`，来自 [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)）预装了一些软件包，如 Python 和 Node.js，但可能需要默认安装其他软件。

你有两个自定义选项：

1. 使用已有的镜像，其中包含所需的软件。
2. 创建你自己的自定义 Docker 镜像。

如果你选择第一个选项，可以跳过"创建你的 Docker 镜像"部分。

## 创建你的 Docker 镜像

要创建自定义 Docker 镜像，它必须基于 Debian。

例如，如果你想让 OpenHands 安装 `ruby`，创建一个包含以下内容的 `Dockerfile`：

```dockerfile
FROM debian:latest

# Install required packages
RUN apt-get update && apt-get install -y ruby
```

将此文件保存在一个文件夹中。然后，通过在终端中导航到该文件夹并运行以下命令来构建你的 Docker 镜像（例如，名为 custom-image）：

```bash
docker build -t custom-image .
```

这将生成一个名为 `custom-image` 的新镜像，该镜像将在 Docker 中可用。

> 请注意，在本文档描述的配置中，OpenHands 将以用户 "openhands" 的身份在沙箱内运行，因此通过 docker 文件安装的所有软件包应该对系统上的所有用户可用，而不仅仅是 root。

## 使用开发工作流

### 设置

首先，按照 [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) 中的说明，确保你可以运行 OpenHands。

### 指定基础沙箱镜像

在 OpenHands 目录中的 `config.toml` 文件中，将 `sandbox_base_container_image` 设置为你要使用的镜像。这可以是你已经拉取的镜像或你构建的镜像：

```bash
[core]
...
sandbox_base_container_image="custom-image"
```

### 运行

通过在顶层目录中运行 ```make run``` 来运行 OpenHands。

## 技术解释

请参阅[运行时文档的自定义 docker 镜像部分](https://docs.all-hands.dev/modules/usage/architecture/runtime#advanced-how-openhands-builds-and-maintains-od-runtime-images)以获取更多详细信息。
