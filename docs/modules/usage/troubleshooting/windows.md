# Notes for Windows and WSL Users

OpenDevin only supports Windows via [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Please be sure to run all commands inside your WSL terminal.

## Troubleshooting

### Failed to create opendevin user

If you encounter the following error during setup: `Exception: Failed to create opendevin user in sandbox: b'useradd: UID 0 is not unique\n'`.
You can resolve it by running:
`    export SANDBOX_USER_ID=1000
   `

### Poetry Installation

If you face issues running Poetry even after installing it during the build process, you may need to add its binary path to your environment:
`    export PATH="$HOME/.local/bin:$PATH"
   `

### NoneType object has no attribute 'request'

If you are experiencing issues related to networking, such as `NoneType object has no attribute 'request'` when executing `make run`, you may need to configure your WSL2 networking settings. Follow these steps:

- Open or create the `.wslconfig` file located at `C:\Users\%username%\.wslconfig` on your Windows host machine.
- Add the following configuration to the `.wslconfig` file:

```
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

- Save the `.wslconfig` file.
- Restart WSL2 completely by exiting any running WSL2 instances and executing the command `wsl --shutdown` in your command prompt or terminal.
- After restarting WSL, attempt to execute `make run` again. The networking issue should be resolved.
