# 🚧 Troubleshooting

:::tip
OpenHands only supports Windows via WSL. Please be sure to run all commands inside your WSL terminal.
:::

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
