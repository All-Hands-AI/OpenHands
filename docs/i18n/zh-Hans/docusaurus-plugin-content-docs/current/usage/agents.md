---
sidebar_position: 3
---

# 🧠 Agents and Capabilities

## CodeAct Agent

### 描述

该Agent实现了CodeAct的思想（[论文](https://arxiv.org/abs/2402.01030)，[推特](https://twitter.com/xingyaow_/status/1754556835703751087)），将LLM agents的**行为**合并到一个统一的**代码**动作空间中，以实现_简化_和_性能_（详情见论文）。

概念理念如下图所示。在每个回合，Agent可以：

1. **对话**：用自然语言与人类交流，进行澄清、确认等。
2. **CodeAct**：选择通过执行代码来完成任务

- 执行任何有效的Linux `bash`命令
- 使用[交互式Python解释器](https://ipython.org/)执行任何有效的 `Python`代码。这是通过`bash`命令模拟的，详细信息请参见插件系统。

![image](https://github.com/OpenDevin/OpenDevin/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

### 插件系统

为了使CodeAct agent在仅能访问`bash`动作空间时更强大，CodeAct agent利用了OpenDevin的插件系统：

- [Jupyter插件](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/jupyter)：通过bash命令实现IPython执行
- [SWE-agent工具插件](https://github.com/OpenDevin/OpenDevin/tree/main/opendevin/runtime/plugins/swe_agent_commands)：为软件开发任务引入的强大bash命令行工具，由[swe-agent](https://github.com/princeton-nlp/swe-agent)提供。

### 演示

https://github.com/OpenDevin/OpenDevin/assets/38853559/f592a192-e86c-4f48-ad31-d69282d5f6ac

_CodeActAgent使用`gpt-4-turbo-2024-04-09`执行数据科学任务（线性回归）的示例_

### 动作

`Action`,
`CmdRunAction`,
`IPythonRunCellAction`,
`AgentEchoAction`,
`AgentFinishAction`,
`AgentTalkAction`

### 观测

`CmdOutputObservation`,
`IPythonRunCellObservation`,
`AgentMessageObservation`,
`UserMessageObservation`

### 方法

| 方法           | 描述                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `__init__`     | 使用`llm`和一系列信息`list[Mapping[str, str]]`初始化Agent                                                                                  |
| `step`         | 使用CodeAct Agent执行一步操作，包括收集前一步的信息并提示模型执行命令。                                                                     |
| `search_memory`| 尚未实现                                                                                                                                    |

### 进行中的工作 & 下一步

[] 支持Web浏览
[] 完成CodeAct agent提交Github PR的工作流程

## Monologue Agent

### 描述

Monologue Agent利用长短期记忆来完成任务。
长期记忆存储为LongTermMemory对象，模型使用它来搜索过去的示例。
短期记忆存储为Monologue对象，模型可以根据需要进行压缩。

### 动作

`Action`,
`NullAction`,
`CmdRunAction`,
`FileWriteAction`,
`FileReadAction`,
`AgentRecallAction`,
`BrowseURLAction`,
`GithubPushAction`,
`AgentThinkAction`

### 观测

`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`

### 方法

| 方法           | 描述                                                                                                                                       |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `__init__`     | 使用长期记忆和内部独白初始化Agent                                                                                                            |
| `_add_event`   | 将事件附加到Agent的独白中，如独白过长自动与摘要一起压缩                                                                                    |
| `_initialize`  | 使用`INITIAL_THOUGHTS`列表为agent提供其能力的上下文以及如何导航`/workspace`                                                                 |
| `step`         | 通过添加最近的动作和观测修改当前状态，然后提示模型考虑其接下来的动作。                                                                     |
| `search_memory`| 使用`VectorIndexRetriever`在长期记忆中查找相关记忆。                                                                                         |

## Planner Agent

### 描述

Planner agent利用特殊的提示策略为解决问题创建长期计划。
在每一步中，Agent会获得其先前的动作-观测对、当前任务以及基于上一次操作提供的提示。

### 动作

`NullAction`,
`CmdRunAction`,
`BrowseURLAction`,
`GithubPushAction`,
`FileReadAction`,
`FileWriteAction`,
`AgentRecallAction`,
`AgentThinkAction`,
`AgentFinishAction`,
`AgentSummarizeAction`,
`AddTaskAction`,
`ModifyTaskAction`

### 观测

`Observation`,
`NullObservation`,
`CmdOutputObservation`,
`FileReadObservation`,
`AgentRecallObservation`,
`BrowserOutputObservation`

### 方法

| 方法           | 描述                                                                                                                                                                                   |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__`     | 使用`llm`初始化Agent                                                                                                                                                                   |
| `step`         | 检查当前步骤是否完成，如果是则返回`AgentFinishAction`。否则，创建计划提示并发送给模型进行推理，将结果作为下一步动作。                                                                      |
| `search_memory`| 尚未实现                                                                                                                                                                               |
