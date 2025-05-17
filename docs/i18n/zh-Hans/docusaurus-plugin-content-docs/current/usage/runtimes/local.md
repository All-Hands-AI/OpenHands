# 本地运行时

本地运行时允许OpenHands代理直接在您的本地机器上执行操作，无需使用Docker。
这种运行时主要用于受控环境，如CI流水线或Docker不可用的测试场景。

:::caution
**安全警告**：本地运行时在没有任何沙箱隔离的情况下运行。代理可以直接访问和修改
您机器上的文件。仅在受控环境中或当您完全理解安全影响时使用此运行时。
:::

## 前提条件

在使用本地运行时之前，请确保：

1. 您可以使用[开发工作流](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)运行OpenHands。
2. 您的系统上有tmux可用。

## 配置

要使用本地运行时，除了必需的配置（如LLM提供商、模型和API密钥）外，您还需要在启动OpenHands时通过环境变量或[config.toml文件](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)设置以下选项：

通过环境变量：

```bash
# 必需
export RUNTIME=local

# 可选但推荐
# 代理默认在/workspace中工作，所以将您的项目目录挂载到那里
export SANDBOX_VOLUMES=/path/to/your/workspace:/workspace:rw
# 对于只读数据，使用不同的挂载路径
# export SANDBOX_VOLUMES=/path/to/your/workspace:/workspace:rw,/path/to/large/dataset:/data:ro
```

通过`config.toml`：

```toml
[core]
runtime = "local"

[sandbox]
# 代理默认在/workspace中工作，所以将您的项目目录挂载到那里
volumes = "/path/to/your/workspace:/workspace:rw"
# 对于只读数据，使用不同的挂载路径
# volumes = "/path/to/your/workspace:/workspace:rw,/path/to/large/dataset:/data:ro"
```

如果未设置`SANDBOX_VOLUMES`，运行时将创建一个临时目录供代理工作。

## 使用示例

以下是如何在无头模式下使用本地运行时启动OpenHands的示例：

```bash
# 将运行时类型设置为local
export RUNTIME=local

# 设置工作区目录（代理默认在/workspace中工作）
export SANDBOX_VOLUMES=/path/to/your/project:/workspace:rw
# 对于您不希望代理修改的只读数据，使用不同的路径
# export SANDBOX_VOLUMES=/path/to/your/project:/workspace:rw,/path/to/reference/data:/data:ro

# 启动OpenHands
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

## 使用场景

本地运行时特别适用于：

- Docker不可用的CI/CD流水线。
- OpenHands本身的测试和开发。
- 容器使用受限的环境。
