# 仓库自定义

您可以通过在根目录创建一个 `.openhands` 目录来自定义 OpenHands 与您的仓库的交互方式。

## 微代理

微代理允许您使用特定于项目的信息扩展 OpenHands 提示，并定义 OpenHands 应该如何运行。有关更多信息，请参阅[微代理概述](../prompting/microagents-overview)。


## 设置脚本
您可以添加一个 `.openhands/setup.sh` 文件，该文件将在 OpenHands 每次开始处理您的仓库时运行。
这是安装依赖项、设置环境变量和执行其他设置任务的理想位置。

例如：
```bash
#!/bin/bash
export MY_ENV_VAR="my value"
sudo apt-get update
sudo apt-get install -y lsof
cd frontend && npm install ; cd ..
```
