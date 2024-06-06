---
sidebar_position: 5
---

# 🚧 Troubleshooting

There are some error messages that frequently get reported by users.

We'll try to make the install process easier and these error messages
better in the future. But for now, you can look for your error message below and see if there are any workarounds.

For each of these error messages **there is an existing issue**. Please do not
open a new issue--just comment there.

If you find more information or a workaround for one of these issues, please
open a *PR* to add details to this file.

:::tip
If you're running on Windows and having trouble, check out our [guide for Windows (WSL) users](troubleshooting/windows).
:::

## Unable to connect to Docker

[GitHub Issue](https://github.com/OpenDevin/OpenDevin/issues/1226)

### Symptoms

```bash
Error creating controller. Please check Docker is running and visit `https://opendevin.github.io/OpenDevin/modules/usage/troubleshooting` for more debugging information.
```

```bash
docker.errors.DockerException: Error while fetching server API version: ('Connection aborted.', FileNotFoundError(2, 'No such file or directory'))
```

### Details

OpenDevin uses a Docker container to do its work safely, without potentially breaking your machine.

### Workarounds

* Run `docker ps` to ensure that docker is running
* Make sure you don't need `sudo` to run docker [see here](https://www.baeldung.com/linux/docker-run-without-sudo)
* If you are on a Mac, check the [permissions requirements](https://docs.docker.com/desktop/mac/permission-requirements/) and in particular consider enabling the `Allow the default Docker socket to be used` under `Settings > Advanced` in Docker Desktop.
* In addition, upgrade your Docker to the latest version under `Check for Updates`

## Unable to connect to SSH box

[GitHub Issue](https://github.com/OpenDevin/OpenDevin/issues/1156)

### Symptoms

```python
self.shell = DockerSSHBox(
...
pexpect.pxssh.ExceptionPxssh: Could not establish connection to host
```

### Details

By default, OpenDevin connects to a running container using SSH. On some machines,
especially Windows, this seems to fail.

### Workarounds

* Restart your computer (sometimes it does work)
* Be sure to have the latest versions of WSL and Docker
* Check that your distribution in WSL is up to date as well
* Try [this reinstallation guide](https://github.com/OpenDevin/OpenDevin/issues/1156#issuecomment-2064549427)
* Set `-e SANDBOX_TYPE=exec` to switch to the ExecBox docker container

## Unable to connect to LLM

[GitHub Issue](https://github.com/OpenDevin/OpenDevin/issues/1208)

### Symptoms

```python
  File "/app/.venv/lib/python3.12/site-packages/openai/_exceptions.py", line 81, in __init__
    super().__init__(message, response.request, body=body)
                              ^^^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'request'
```

### Details

[GitHub Issues](https://github.com/OpenDevin/OpenDevin/issues?q=is%3Aissue+is%3Aopen+404)

This usually happens with *local* LLM setups, when OpenDevin can't connect to the LLM server.
See our guide for [local LLMs](llms/localLLMs) for more information.

### Workarounds

* Check your `base_url` in your config.toml (if it exists) under the "llm" section
* Check that ollama (or whatever LLM you're using) is running OK
* Make sure you're using `--add-host host.docker.internal:host-gateway` when running in Docker

## `404 Resource not found`

### Symptoms

```python
Traceback (most recent call last):
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 414, in completion
    raise e
  File "/app/.venv/lib/python3.12/site-packages/litellm/llms/openai.py", line 373, in completion
    response = openai_client.chat.completions.create(**data, timeout=timeout)  # type: ignore
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_utils/_utils.py", line 277, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/resources/chat/completions.py", line 579, in create
    return self._post(
           ^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1232, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 921, in request
    return self._request(
           ^^^^^^^^^^^^^^
  File "/app/.venv/lib/python3.12/site-packages/openai/_base_client.py", line 1012, in _request
    raise self._make_status_error_from_response(err.response) from None
openai.NotFoundError: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
```

### Details

This happens when LiteLLM (our library for connecting to different LLM providers) can't find
the API endpoint you're trying to connect to. Most often this happens for Azure or ollama users.

### Workarounds

* Check that you've set `LLM_BASE_URL` properly
* Check that model is set properly, based on the [LiteLLM docs](https://docs.litellm.ai/docs/providers)
  * If you're running inside the UI, be sure to set the `model` in the settings modal
  * If you're running headless (via main.py) be sure to set `LLM_MODEL` in your env/config
* Make sure you've followed any special instructions for your LLM provider
  * [ollama](/OpenDevin/modules/usage/llms/localLLMs)
  * [Azure](/OpenDevin/modules/usage/llms/azureLLMs)
  * [Google](/OpenDevin/modules/usage/llms/googleLLMs)
* Make sure your API key is correct
* See if you can connect to the LLM using `curl`
* Try [connecting via LiteLLM directly](https://github.com/BerriAI/litellm) to test your setup

## `make build` getting stuck on package installations

### Symptoms

Package installation stuck on `Pending...` without any error message:

```bash
Package operations: 286 installs, 0 updates, 0 removals

  - Installing certifi (2024.2.2): Pending...
  - Installing h11 (0.14.0): Pending...
  - Installing idna (3.7): Pending...
  - Installing sniffio (1.3.1): Pending...
  - Installing typing-extensions (4.11.0): Pending...
```

### Details

In rare cases, `make build` can seemingly get stuck on package installations
without any error message.

### Workarounds

* The package installer Poetry may miss a configuration setting for
where credentials are to be looked up (keyring).

### Workaround

First check with `env` if a value for `PYTHON_KEYRING_BACKEND` exists.
If not, run the below command to set it to a known value and retry the build:

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

## Sessions are not restored

### Symptoms

OpenDevin usually asks whether to resume or start a new session when opening the UI.
But clicking "Resume" still starts a fresh new chat.

### Details

With a standard installation as of today session data is stored in memory.
Currently, if OpenDevin's service is restarted, previous sessions become
invalid (a new secret is generated) and thus not recoverable.

### Workarounds

* Change configuration to make sessions persistent by editing the `config.toml`
file (in OpenDevin's root folder) by specifying a `file_store` and an
absolute `file_store_path`:

```toml
file_store="local"
file_store_path="/absolute/path/to/opendevin/cache/directory"
```

* Add a fixed jwt secret in your .bashrc, like below, so that previous session id's
should stay accepted.

```bash
EXPORT JWT_SECRET=A_CONST_VALUE
```
