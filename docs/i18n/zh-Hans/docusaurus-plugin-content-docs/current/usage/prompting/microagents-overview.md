# 微代理概述

微代理是专门的提示，通过领域特定知识增强OpenHands的能力。
它们提供专家指导，自动化常见任务，并确保项目间的实践一致性。

## 微代理类型

目前OpenHands支持以下类型的微代理：

- [通用仓库微代理](./microagents-repo)：关于仓库的OpenHands通用指南。
- [关键词触发微代理](./microagents-keyword)：通过提示中的特定关键词激活的指南。

要自定义OpenHands的行为，请在仓库根目录创建.openhands/microagents/目录，并在其中添加`<microagent_name>.md`文件。

:::note
加载的微代理会占用上下文窗口的空间。
这些微代理与用户消息一起，为OpenHands提供有关任务和环境的信息。
:::

仓库结构示例：

```
some-repository/
└── .openhands/
    └── microagents/
        └── repo.md            # 通用仓库指南
        └── trigger_this.md    # 由特定关键词触发的微代理
        └── trigger_that.md    # 由特定关键词触发的微代理
```

## 微代理前置元数据要求

每个微代理文件可能包含提供额外信息的前置元数据。在某些情况下，这些前置元数据是必需的：

| 微代理类型 | 是否必需 |
|------------|----------|
| `通用仓库微代理` | 否 |
| `关键词触发微代理` | 是 |
