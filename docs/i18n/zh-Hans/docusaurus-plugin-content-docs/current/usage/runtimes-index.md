# 运行时配置

:::note
本节适用于希望使用Docker以外的运行时环境来运行OpenHands的用户。
:::

运行时是OpenHands代理可以编辑文件和运行命令的环境。

默认情况下，OpenHands使用[基于Docker的运行时](./runtimes/docker)，在您的本地计算机上运行。
这意味着您只需要为所使用的LLM付费，而且您的代码只会发送给LLM。

我们还支持其他运行时，这些通常由第三方管理。

此外，我们提供了一个[本地运行时](./runtimes/local)，可以直接在您的机器上运行而无需Docker，
这在CI流水线等受控环境中非常有用。

## 可用的运行时

OpenHands支持几种不同的运行时环境：

- [Docker运行时](./runtimes/docker.md) - 默认运行时，使用Docker容器进行隔离（推荐大多数用户使用）。
- [OpenHands远程运行时](./runtimes/remote.md) - 用于并行执行的云端运行时（测试版）。
- [Modal运行时](./runtimes/modal.md) - 由我们的合作伙伴Modal提供的运行时。
- [Daytona运行时](./runtimes/daytona.md) - 由Daytona提供的运行时。
- [本地运行时](./runtimes/local.md) - 无需Docker直接在本地机器上执行。
