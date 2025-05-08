# 全局微代理

## 概述

全局微代理是适用于所有OpenHands用户的[关键词触发微代理](./microagents-keyword)。当前全局微代理的列表可以在[OpenHands仓库](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents)中找到。

## 贡献全局微代理

您可以创建全局微代理并通过向官方仓库提交拉取请求与社区分享。

有关如何为OpenHands做出贡献的具体说明，请参阅[CONTRIBUTING.md](https://github.com/All-Hands-AI/OpenHands/blob/main/CONTRIBUTING.md)。

### 全局微代理最佳实践

- **明确范围**：保持微代理专注于特定领域或任务。
- **明确指令**：提供清晰、明确的指导方针。
- **有用的示例**：包含常见用例的实用示例。
- **安全第一**：包含必要的警告和约束。
- **集成意识**：考虑微代理如何与其他组件交互。

### 贡献全局微代理的步骤

#### 1. 规划全局微代理

在创建全局微代理之前，请考虑：

- 它将解决什么特定问题或用例？
- 它应该具有哪些独特的能力或知识？
- 哪些触发词适合激活它？
- 它应该遵循哪些约束或指导方针？

#### 2. 创建文件

在适当的目录中创建一个具有描述性名称的新Markdown文件：
[`microagents/`](https://github.com/All-Hands-AI/OpenHands/tree/main/microagents)

#### 3. 测试全局微代理

- 使用各种提示测试代理。
- 验证触发词是否正确激活代理。
- 确保指令清晰全面。
- 检查与现有代理的潜在冲突和重叠。

#### 4. 提交流程

提交拉取请求，包括：

- 新的微代理文件。
- 如有需要，更新文档。
- 描述代理的目的和功能。
