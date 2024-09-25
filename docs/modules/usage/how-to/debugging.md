# Debugging

The following is intended as a primer on debugging OpenHands for Development purposes.

## Uvicorn Hates Your Workspace Directory

Uvicorn currently *ALWAYS* adds the current working directory to the list of reload directories, regardless of what
is specified in `reload-dir`. (Their docs are inaccurate at the moment too!). The `--exclude-list` / `--include-list` 
directives do not reliably filter out files based on a directory. (They could if you could specify an absolute path,
but uvicorn does not allow this.)

So the only real option for now is to make sure your workspace directory is *OUTSIDE* the openhands directory. (e.g.:
update the following in your `config.toml` : `workspace_base = "../workspace"`) Otherwise every time you modify a python
file in a subdirectory of your workspace directory, uvicorn will blast your session and create a new one. (I tried
many combinations of `workspace/*` / `**/workspace/**` before giving up)

## Server / VSCode

The following `launch.json` will allow debugging the agent, controller and server elements, but not the sandbox (Which
runs inside docker):

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
                "--port",
                "3000"
            ],
            "justMyCode": false
        }
    ]
}
```