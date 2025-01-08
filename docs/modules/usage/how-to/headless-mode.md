# Headless Mode

You can run OpenHands with a single command, without starting the web application.
This makes it easy to write scripts and automate tasks with OpenHands.

This is different from [CLI Mode](cli-mode), which is interactive, and better for active development.

## With Python

To run OpenHands in headless mode with Python:
1. Ensure you have followed the [Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. Run the following command:
```bash
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

You'll need to be sure to set your model, API key, and other settings via environment variables
[or the `config.toml` file](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml).

## With Docker

To run OpenHands in Headless mode with Docker:

1. Set the following environmental variables in your terminal:

- `WORKSPACE_BASE` to the directory you want OpenHands to edit (Ex: `export WORKSPACE_BASE=$(pwd)/workspace`).
- `LLM_MODEL` to the model to use (Ex: `export LLM_MODEL="anthropic/claude-3-5-sonnet-20241022"`).
- `LLM_API_KEY` to the API key (Ex: `export LLM_API_KEY="sk_test_12345"`).

2. Run the following Docker command:

```bash
docker run -it \
    --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.19-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_API_KEY=$LLM_API_KEY \
    -e LLM_MODEL=$LLM_MODEL \
    -e LOG_ALL_EVENTS=true \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands-state:/.openhands-state \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    docker.all-hands.dev/all-hands-ai/openhands:0.19 \
    python -m openhands.core.main -t "write a bash script that prints hi"
```

## Advanced Headless Configurations

To view all available configuration options for headless mode, run the Python command with the `--help` flag.

### Additional Logs

For the headless mode to log all the agent actions, in the terminal run: `export LOG_ALL_EVENTS=true`
