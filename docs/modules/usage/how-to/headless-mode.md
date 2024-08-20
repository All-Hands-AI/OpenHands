# Running in Headless Mode

You can run OpenHands via a CLI, without starting the web application. This makes it easy
to automate tasks with OpenHands.

## With Python
To run OpenHands in headless mode with Python,
[follow the Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md),
and then run:

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

## With Docker
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
    ghcr.io/all-hands-ai/openhands:main \ # TODO: pin a version here
    python -m openhands.core.main \
    -t "Write a bash script that prints Hello World"
```
