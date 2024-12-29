# 🚧 Troubleshooting

:::tip
OpenHands only supports Windows via WSL. Please be sure to run all commands inside your WSL terminal.
:::

## Common Docker Errors

It's possible you received an error from Docker when you tried to run `./start_openhands.sh`, there are two main reasons for this.

### Docker Permission Denied Error

> docker: Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Post http://%2Fvar%2Frun%2Fdocker.sock/v1.35/containers/create: dial unix /var/run/docker.sock: connect: permission denied. See 'docker run --help'.

This error is because your account was not properly setup to run Docker without `sudo` permissions. You can find the instructions for fixing this in the Docker documentation on [Linux post-installation steps for Docker Engine](https://docs.docker.com/engine/install/linux-postinstall/)

### Docker Address Already in Use Error

> docker: Error response from daemon: driver failed programming external connectivity on endpoint openhands-app (4861aeaf94495bdc51444d2659579f03f705445393624e414b826c95558e2f46): failed to bind port :::3000/tcp: Error starting userland proxy: listen tcp6 [::]:3000: bind: address already in use.

This error occurs because you have another application or service using the port you configured in `start_openhands.sh` as your `LOCAL_PORT`, change this to another port number >1024 and try again.

### Docker Client Failed

>Launch docker client failed. Please make sure you have installed docker and started docker desktop/daemon.

Either docker is not installed or it is not being found on your $PATH.

Try the following stpes in order:

* Confirm `docker` is running on your system. You should be able to run `docker ps` in the terminal successfully.
* If using Docker Desktop
    * Ensure `Settings > Advanced > Allow the default Docker socket to be used` is enabled.
    * Depending on your configuration, you may need `Settings > Resources > Network > Enable host networking` enabled.
* Reinstall Docker Desktop or Docker Engine

---

## Development Workflow Specific

This section is specific to local deployment used for Developers and can be ignored if you're using the Docker installation method.

### Error building runtime docker image

When attempting to start a new session it fails, and errors with terms like the following appearing in the logs:

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
