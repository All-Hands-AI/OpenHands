# Local Runtime

The Local Runtime allows the OpenHands agent to execute actions directly on your local machine without using Docker.
This runtime is primarily intended for controlled environments like CI pipelines or testing scenarios where Docker is not available.

:::caution
**Security Warning**: The Local Runtime runs without any sandbox isolation. The agent can directly access and modify
files on your machine. Only use this runtime in controlled environments or when you fully understand the security implications.
:::

## Prerequisites

Before using the Local Runtime, ensure that:

1. You can run OpenHands using the [Development workflow](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. tmux is available on your system.

## Configuration

To use the Local Runtime, besides required configurations like the LLM provider, model and API key, you'll need to set
the following options via environment variables or the [config.toml file](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml) when starting OpenHands:

Via environment variables:

```bash
# Required
export RUNTIME=local

# Optional but recommended
export WORKSPACE_BASE=/path/to/your/workspace
```

Via `config.toml`:

```toml
[core]
runtime = "local"
workspace_base = "/path/to/your/workspace"
```

If `WORKSPACE_BASE` is not set, the runtime will create a temporary directory for the agent to work in.

## Example Usage

Here's an example of how to start OpenHands with the Local Runtime in Headless Mode:

```bash
# Set the runtime type to local
export RUNTIME=local

# Optionally set a workspace directory
export WORKSPACE_BASE=/path/to/your/project

# Start OpenHands
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

## Use Cases

The Local Runtime is particularly useful for:

- CI/CD pipelines where Docker is not available.
- Testing and development of OpenHands itself.
- Environments where container usage is restricted.
