# 🧠 主代理和能力

## CodeActAgent

### 描述

这个代理实现了 CodeAct 的思想（[论文](https://arxiv.org/abs/2402.01030)，[推文](https://twitter.com/xingyaow_/status/1754556835703751087)），将 LLM 代理的**行动**整合到一个统一的**代码**行动空间中，以实现_简单性_和_性能_。

概念思想如下图所示。在每一轮中，代理可以：

1. **对话**：用自然语言与人类交流，以寻求澄清、确认等。
2. **CodeAct**：选择通过执行代码来执行任务

- 执行任何有效的 Linux `bash` 命令
- 使用 [交互式 Python 解释器](https://ipython.org/) 执行任何有效的 `Python` 代码。这是通过 `bash` 命令模拟的，有关更多详细信息，请参阅下面的插件系统。

![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### 演示

https://github.com/All-Hands-AI/OpenHands/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_使用 `gpt-4-turbo-2024-04-09` 的 CodeActAgent 执行数据科学任务（线性回归）的示例_。
