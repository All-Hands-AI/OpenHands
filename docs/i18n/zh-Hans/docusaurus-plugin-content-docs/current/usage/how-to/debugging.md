以下是翻译后的内容:

# 调试

以下内容旨在作为开发目的下调试 OpenHands 的入门指南。

## 服务器 / VSCode

以下 `launch.json` 将允许调试 agent、controller 和 server 元素,但不包括 sandbox(它运行在 docker 内)。它将忽略 `workspace/` 目录内的任何更改:

```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "OpenHands CLI",
            "type": "debugpy",
            "request": "launch",
            "module": "openhands.core.cli",
            "justMyCode": false
        },
        {
            "name": "OpenHands WebApp",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "openhands.server.listen:app",
                "--reload",
                "--reload-exclude",
                "${workspaceFolder}/workspace",
                "--port",
                "3000"
            ],
            "justMyCode": false
        }
    ]
}
```

可以指定更具体的调试配置,其中包括更多参数:

```
    ...
    {
      "name": "Debug CodeAct",
      "type": "debugpy",
      "request": "launch",
      "module": "openhands.core.main",
      "args": [
        "-t",
        "Ask me what your task is.",
        "-d",
        "${workspaceFolder}/workspace",
        "-c",
        "CodeActAgent",
        "-l",
        "llm.o1",
        "-n",
        "prompts"
      ],
      "justMyCode": false
    }
    ...
```

上面代码片段中的值可以更新,例如:

    * *t*: 任务
    * *d*: openhands 工作区目录
    * *c*: agent
    * *l*: LLM 配置 (在 config.toml 中预定义)
    * *n*: 会话名称 (例如 eventstream 名称)
