# 🚧 Troubleshooting

:::tip
OpenHands only supports Windows via WSL. Please be sure to run all commands inside your WSL terminal.
:::

### Unable to access VS Code tab via local IP

**Description**

When accessing OpenHands through a non-localhost URL (such as a LAN IP address), the VS Code tab shows a "Forbidden" error, while other parts of the UI work fine.

**Resolution**

This happens because VS Code runs on a random high port that may not be exposed or accessible from other machines. To fix this:

1. Set a specific port for VS Code using the `SANDBOX_VSCODE_PORT` environment variable:
   ```bash
   docker run -it --rm \
       -e SANDBOX_VSCODE_PORT=41234 \
       -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:latest \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.openhands-state:/.openhands-state \
       -p 3000:3000 \
       -p 41234:41234 \
       --add-host host.docker.internal:host-gateway \
       --name openhands-app \
       docker.all-hands.dev/all-hands-ai/openhands:latest
   ```

2. Make sure to expose the same port with `-p 41234:41234` in your Docker command.

3. Alternatively, you can set this in your `config.toml` file:
   ```toml
   [sandbox]
   vscode_port = 41234
   ```

### Launch docker client failed

**Description**

When running OpenHands, the following error is seen:
```
Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.
```

**Resolution**

Try these in order:
* Confirm `docker` is running on your system. You should be able to run `docker ps` in the terminal successfully.
* If using Docker Desktop, ensure `Settings > Advanced > Allow the default Docker socket to be used` is enabled.
* Depending on your configuration you may need `Settings > Resources > Network > Enable host networking` enabled in Docker Desktop.
* Reinstall Docker Desktop.

### Permission Error

**Description**

On initial prompt, an error is seen with `Permission Denied` or `PermissionError`.

**Resolution**

* Check if the `~/.openhands-state` is owned by `root`. If so, you can:
  * Change the directory's ownership: `sudo chown <user>:<user> ~/.openhands-state`.
  * or update permissions on the directory: `sudo chmod 777 ~/.openhands-state`
  * or delete it if you don’t need previous data. OpenHands will recreate it. You'll need to re-enter LLM settings.
* If mounting a local directory, ensure your `WORKSPACE_BASE` has the necessary permissions for the user running
  OpenHands.
