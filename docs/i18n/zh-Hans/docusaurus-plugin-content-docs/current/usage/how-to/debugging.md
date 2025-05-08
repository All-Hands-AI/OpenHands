# 调试

以下内容旨在作为开发目的调试 OpenHands 的入门指南。

## 服务器 / VSCode

以下 `launch.json` 将允许调试代理、控制器和服务器元素，但不包括沙盒（在 Docker 内运行）。它将忽略 `workspace/` 目录内的任何更改：

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

可以指定包含更多参数的更具体的调试配置：

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

上面代码片段中的值可以更新，使得：

    * *t*：任务
    * *d*：openhands 工作空间目录
    * *c*：代理
    * *l*：LLM 配置（在 config.toml 中预定义）
    * *n*：会话名称（例如 eventstream 名称）
