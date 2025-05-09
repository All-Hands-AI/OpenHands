# 🧠 主代理和能力

## CodeActAgent

### 描述

该代理实现了CodeAct理念（[论文](https://arxiv.org/abs/2402.01030)，[推文](https://twitter.com/xingyaow_/status/1754556835703751087)），将LLM代理的**行动**整合到统一的**代码**行动空间中，以实现_简洁性_和_性能_。

概念性的想法如下图所示。在每个回合中，代理可以：

1. **对话**：用自然语言与人类交流，以寻求澄清、确认等。
2. **CodeAct**：选择通过执行代码来执行任务

- 执行任何有效的Linux `bash`命令
- 通过[交互式Python解释器](https://ipython.org/)执行任何有效的`Python`代码。这是通过`bash`命令模拟实现的，更多详情请参见下面的插件系统。

![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### 演示

https://github.com/All-Hands-AI/OpenHands/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_使用`gpt-4-turbo-2024-04-09`的CodeActAgent执行数据科学任务（线性回归）的示例_。
