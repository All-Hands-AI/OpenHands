# 自定义沙盒

:::note
本指南适用于希望为运行时使用自己的自定义Docker镜像的用户。例如，预装了特定工具或编程语言的镜像。
:::

沙盒是代理执行任务的地方。代理不会直接在您的计算机上运行命令（这可能有风险），而是在Docker容器内运行它们。

默认的OpenHands沙盒（来自[nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)的`python-nodejs:python3.12-nodejs22`）预装了一些软件包，如Python和Node.js，但可能需要默认安装其他软件。

您有两种自定义选项：

- 使用已有的、包含所需软件的镜像。
- 创建您自己的自定义Docker镜像。

如果您选择第一个选项，可以跳过`创建您的Docker镜像`部分。

## 创建您的Docker镜像

要创建自定义Docker镜像，它必须基于Debian。

例如，如果您希望OpenHands预装`ruby`，您可以创建一个包含以下内容的`Dockerfile`：

```dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# Install required packages
RUN apt-get update && apt-get install -y ruby
```

或者您可以使用特定于Ruby的基础镜像：

```dockerfile
FROM ruby:latest
```

将此文件保存在一个文件夹中。然后，通过在终端中导航到该文件夹并运行以下命令来构建您的Docker镜像（例如，命名为custom-image）：
```bash
docker build -t custom-image .
```

这将生成一个名为`custom-image`的新镜像，该镜像将在Docker中可用。

## 使用Docker命令

使用[docker命令](/modules/usage/installation#start-the-app)运行OpenHands时，将`-e SANDBOX_RUNTIME_CONTAINER_IMAGE=...`替换为`-e SANDBOX_BASE_CONTAINER_IMAGE=<自定义镜像名称>`：

```commandline
docker run -it --rm --pull=always \
    -e SANDBOX_BASE_CONTAINER_IMAGE=custom-image \
    ...
```

## 使用开发工作流程

### 设置

首先，确保您可以按照[Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)中的说明运行OpenHands。

### 指定基础沙盒镜像

在OpenHands目录中的`config.toml`文件中，将`base_container_image`设置为您想要使用的镜像。这可以是您已经拉取的镜像或您构建的镜像：

```bash
[core]
...
[sandbox]
base_container_image="custom-image"
```

### 其他配置选项

`config.toml`文件支持多种其他选项来自定义您的沙盒：

```toml
[core]
# 在构建运行时安装额外的依赖项
# 可以包含任何有效的shell命令
# 如果您在这些命令中需要Python解释器的路径，可以使用$OH_INTERPRETER_PATH变量
runtime_extra_deps = """
pip install numpy pandas
apt-get update && apt-get install -y ffmpeg
"""

# 为运行时设置环境变量
# 对于需要在运行时可用的配置很有用
runtime_startup_env_vars = { DATABASE_URL = "postgresql://user:pass@localhost/db" }

# 为多架构构建指定平台（例如，"linux/amd64"或"linux/arm64"）
platform = "linux/amd64"
```

### 运行

通过在顶级目录中运行```make run```来运行OpenHands。
