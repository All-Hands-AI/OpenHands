# デバッグ

以下は開発目的のためのOpenHandsのデバッグに関する入門ガイドです。

## サーバー / VSCode

以下の`launch.json`を使用すると、エージェント、コントローラー、サーバー要素のデバッグが可能になりますが、サンドボックス（Dockerの中で実行される）はデバッグできません。これは`workspace/`ディレクトリ内の変更を無視します：

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

より多くのパラメータを含む、より具体的なデバッグ設定を指定することもできます：

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

上記のスニペットの値は以下のように更新できます：

    * *t*: タスク
    * *d*: openhandsワークスペースディレクトリ
    * *c*: エージェント
    * *l*: LLM設定（config.tomlで事前定義）
    * *n*: セッション名（例：イベントストリーム名）
