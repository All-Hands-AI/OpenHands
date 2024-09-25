# Debugging

The following is intended as a primer on debugging OpenHands for Development purposes.

## Server / VSCode

The following `launch.json` will allow debugging the agent, controller and server elements, but not the sandbox (Which
runs inside docker). It will watch for changes in the `openhands` directory (So updates to files in your workspace will
not cause uvicorn to reload):

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
                "--reload-include",
                "openhands",
                "--port",
                "3000"
            ],
            "justMyCode": false
        }
    ]
}
```