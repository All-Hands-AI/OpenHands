# Troubleshooting

> If you're running on Windows and having trouble, check out our [guide for Windows users](./Windows.md)

There are some error messages that get reported over and over by users.
We'll try and make the install process easier, and to make these error messages
better in the future. But for now, you can look for your error message below,
and see if there are any workaround.

For each of these error messages **there is an existing issue**. Please do not
open an new issue--just comment there.

If you find more information or a workaround for one of these issues, please
open a PR to add details to this file.

## Unable to connect to docker
https://github.com/OpenDevin/OpenDevin/issues/1226

### Symptoms
```
Error creating controller. Please check Docker is running using docker ps
```
```
docker.errors.DockerException: Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

### Details
OpenDevin uses a docker container to do its work safely, without potentially breaking your machine.

### Workarounds
* Run `docker ps` to ensure that docker is running
* Make sure you don't need `sudo` to run docker [see here](https://www.baeldung.com/linux/docker-run-without-sudo)


## Unable to connect to SSH box
https://github.com/OpenDevin/OpenDevin/issues/1156

### Symptoms
```
self.shell = DockerSSHBox(
...
pexpect.pxssh.ExceptionPxssh: Could not establish connection to host
```

### Details
By default, OpenDevin connects to a running container using SSH. On some machines,
especially Windows, this seems to fail.

### Workarounds
* Restart your computer (sometimes works?)
* Be sure to have the latest versions of WSL and Docker
* Try [this reinstallation guide](https://github.com/OpenDevin/OpenDevin/issues/1156#issuecomment-2064549427)
* Set `-e SANDBOX_TYPE=exec` to switch to the ExecBox docker container

## Unable to connect to LLM
https://github.com/OpenDevin/OpenDevin/issues/1208

### Symptoms
```
  File "/app/.venv/lib/python3.12/site-packages/openai/_exceptions.py", line 81, in __init__
    super().__init__(message, response.request, body=body)
                              ^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'request'
```

### Details
This usually happens with local LLM setups, when OpenDevin can't connect to the LLM server.
See our guide for [local LLMs](./LocalLLMs.md) for more information.

### Workarounds
* Check your `LLM_BASE_URL`
* Check that ollama is running OK
* Make sure you're using `--add-host host.docker.internal=host-gateway` when running in docker
