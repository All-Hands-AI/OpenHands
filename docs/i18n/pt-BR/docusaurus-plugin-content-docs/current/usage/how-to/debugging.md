# Depuração

O seguinte é destinado como uma introdução à depuração do OpenHands para fins de Desenvolvimento.

## Servidor / VSCode

O seguinte `launch.json` permitirá a depuração dos elementos do agente, controlador e servidor, mas não do sandbox (que é executado dentro do docker). Ele ignorará quaisquer alterações dentro do diretório `workspace/`:

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

Configurações de depuração mais específicas que incluem mais parâmetros podem ser especificadas:

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

Os valores no trecho acima podem ser atualizados de modo que:

    * *t*: a tarefa
    * *d*: o diretório de workspace do openhands
    * *c*: o agente
    * *l*: a configuração do LLM (pré-definida em config.toml)
    * *n*: nome da sessão (por exemplo, nome do eventstream)
