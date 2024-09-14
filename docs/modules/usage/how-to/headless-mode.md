# Headless Mode

You can run OpenHands with a single command, without starting the web application.
This makes it easy to write scripts and automate tasks with OpenHands.

This is different from [CLI Mode](cli-mode), which is interactive, and better for active development.

## With Python

To run OpenHands in headless mode with Python,
[follow the Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md),
and then run:

```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

You'll need to be sure to set your model, API key, and other settings via environment variables
[or the `config.toml` file](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## With Docker

1. Set `WORKSPACE_BASE` to the directory you want OpenHands to edit:

```bash
WORKSPACE_BASE=$(pwd)/workspace
```

2. Set `LLM_MODEL` to the model you want to use:

```bash
LLM_MODEL="anthropic/claude-3-5-sonnet-20240620"
```

3. Set `LLM_API_KEY` to your API key:

```bash
LLM_API_KEY="sk_test_12345"
```

4. Run the following Docker command:

```bash
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
    python -m openhands.core.main -t "write a bash script that prints hi"
```
