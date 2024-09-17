# Notes for WSL on Windows Users

OpenHands only supports Windows via [WSL](https://learn.microsoft.com/en-us/windows/wsl/install).
Please be sure to run all commands inside your WSL terminal.

## Troubleshooting

### Recommendation: Do not run as root user

For security reasons, it is highly recommended to not run OpenHands as the root user, but a user with a non-zero UID.

References:

* [Why it is bad to login as root](https://askubuntu.com/questions/16178/why-is-it-bad-to-log-in-as-root)
* [Set default user in WSL](https://www.tenforums.com/tutorials/128152-set-default-user-windows-subsystem-linux-distro-windows-10-a.html#option2)
Hint about the 2nd reference: for Ubuntu users, the command could actually be "ubuntupreview" instead of "ubuntu".

---
### Error: 'docker' could not be found in this WSL 2 distro.

If you are using Docker Desktop, make sure to start it before calling any docker command from inside WSL.
Docker also needs to have the WSL integration option activated.

---
### Poetry Installation

* If you face issues running Poetry even after installing it during the build process, you may need to add its binary path to your environment:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

* If make build stops on an error like this:

```sh
ModuleNotFoundError: no module named <module-name>
```

This could be an issue with Poetry's cache.
Try to run these 2 commands after another:

```sh
rm -r ~/.cache/pypoetry
make build
```

---
### NoneType object has no attribute 'request'

If you are experiencing issues related to networking, such as `NoneType object has no attribute 'request'` when executing `make run`, you may need to configure your WSL2 networking settings. Follow these steps:

* Open or create the `.wslconfig` file located at `C:\Users\%username%\.wslconfig` on your Windows host machine.
* Add the following configuration to the `.wslconfig` file:

```sh
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

* Save the `.wslconfig` file.
* Restart WSL2 completely by exiting any running WSL2 instances and executing the command `wsl --shutdown` in your command prompt or terminal.
* After restarting WSL, attempt to execute `make run` again.
The networking issue should be resolved.
