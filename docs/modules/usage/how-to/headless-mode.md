# Running in Headless / CLI Mode

You can run OpenHands via a CLI, without starting the web application. This makes it easy
to automate tasks with OpenHands. There are 2 main modes of operation:

* **Headless** : Designed for use with scripts
* **CLI** : Designed for interactive use via a console

As with other modes, the environment is configurable via environment variables or by saving values into [config.toml](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml)

## With Python

To run OpenHands in headless mode with Python,
[follow the Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md),
and then run:

### Headless with Python

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

### CLI with Python

```bash
poetry run python -m openhands.core.cli

How can I help? >> write a bash script that prints hi
```

## Headless With Docker

To run OpenHands in headless mode with Docker, run:

```bash
# Set WORKSPACE_BASE to the directory you want OpenHands to edit
WORKSPACE_BASE=$(pwd)/workspace

# Set LLM_API_KEY to an API key, e.g. for OpenAI or Anthropic
LLM_API_KEY="abcde"

# Set LLM_MODEL to the model you want to use
LLM_MODEL="gpt-4o"

docker run -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/all-hands-ai/openhands:0.9 \
    poetry run python -m openhands.core.main \
    -t "Write a bash script that prints Hello World"
```

## CLI With Docker

To run OpenHands in cli mode with Docker, run:

```bash
# Set WORKSPACE_BASE to the directory you want OpenHands to edit
WORKSPACE_BASE=$(pwd)/workspace

# Set LLM_API_KEY to an API key, e.g. for OpenAI or Anthropic
LLM_API_KEY="abcde"

# Set LLM_MODEL to the model you want to use
LLM_MODEL="gpt-4o"

docker run -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/all-hands-ai/openhands:0.9 \
    poetry run python -m openhands.core.cli
```
