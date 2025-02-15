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
---

# Development Workflow Specific
### Error building runtime docker image

**Description**

Attempts to start a new session fail, and errors with terms like the following appear in the logs:
```
debian-security bookworm-security
InRelease At least one invalid signature was encountered.
```

This seems to happen when the hash of an existing external library changes and your local docker instance has
cached a previous version. To work around this, please try the following:

* Stop any containers where the name has the prefix `openhands-runtime-` :
  `docker ps --filter name=openhands-runtime- --filter status=running -aq | xargs docker stop`
* Remove any containers where the name has the prefix `openhands-runtime-` :
  `docker rmi $(docker images --filter name=openhands-runtime- -q --no-trunc)`
* Stop and Remove any containers / images where the name has the prefix `openhands-runtime-`
* Prune containers / images : `docker container prune -f && docker image prune -f`
