# Runtime Configuration

A Runtime is an environment where the OpenHands agent can edit files and run
commands.

By default, OpenHands uses a Docker-based runtime, running on your local computer.
This means you only have to pay for the LLM you're using, and your code is only ever sent to the LLM.

We also support "remote" runtimes, which are typically managed by third-parties.
They can make setup a bit simpler and more scalable, especially
if you're running many OpenHands conversations in parallel (e.g. to do evaluation).

Additionally, we provide a "local" runtime that runs directly on your machine without Docker,
which can be useful in controlled environments like CI pipelines.

## Docker Runtime
This is the default Runtime that's used when you start OpenHands. You might notice
some flags being passed to `docker run` that make this possible:

```
docker run # ...
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.28-nikolaik \
    -v /var/run/docker.sock:/var/run/docker.sock \
    # ...
```

The `SANDBOX_RUNTIME_CONTAINER_IMAGE` from nikolaik is a pre-built runtime image
that contains our Runtime server, as well as some basic utilities for Python and NodeJS.
You can also [build your own runtime image](how-to/custom-sandbox-guide).

### Connecting to Your filesystem
One useful feature here is the ability to connect to your local filesystem. To mount your filesystem into the runtime:
1. Set `WORKSPACE_BASE`:

    ```bash
    export WORKSPACE_BASE=/path/to/your/code

    # Linux and Mac Example
    # export WORKSPACE_BASE=$HOME/OpenHands
    # Will set $WORKSPACE_BASE to /home/<username>/OpenHands
    #
    # WSL on Windows Example
    # export WORKSPACE_BASE=/mnt/c/dev/OpenHands
    # Will set $WORKSPACE_BASE to C:\dev\OpenHands
    ```
2. Add the following options to the `docker run` command:

    ```bash
    docker run # ...
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
        -v $WORKSPACE_BASE:/opt/workspace_base \
        # ...
    ```

Be careful! There's nothing stopping the OpenHands agent from deleting or modifying
any files that are mounted into its workspace.

This setup can cause some issues with file permissions (hence the `SANDBOX_USER_ID` variable)
but seems to work well on most systems.

## OpenHands Remote Runtime

OpenHands Remote Runtime is currently in beta (read [here](https://runtime.all-hands.dev/) for more details), it allows you to launch runtimes in parallel in the cloud.
Fill out [this form](https://docs.google.com/forms/d/e/1FAIpQLSckVz_JFwg2_mOxNZjCtr7aoBFI2Mwdan3f75J_TrdMS1JV2g/viewform) to apply if you want to try this out!

To use the OpenHands Remote Runtime, set the following environment variables when
starting OpenHands:

```bash
docker run # ...
    -e RUNTIME=remote \
    -e SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.app.all-hands.dev" \
    -e SANDBOX_API_KEY="your-all-hands-api-key" \
    -e SANDBOX_KEEP_RUNTIME_ALIVE="true" \
    # ...
```

## Modal Runtime
Our partners at [Modal](https://modal.com/) have also provided a runtime for OpenHands.

To use the Modal Runtime, create an account, and then [create an API key.](https://modal.com/settings)

You'll then need to set the following environment variables when starting OpenHands:
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="your-id" \
    -e MODAL_API_TOKEN_SECRET="your-secret" \
```

## Daytona Runtime

Another option is using [Daytona](https://www.daytona.io/) as a runtime provider:

### Step 1: Retrieve Your Daytona API Key
1. Visit the [Daytona Dashboard](https://app.daytona.io/dashboard/keys).
2. Click **"Create Key"**.
3. Enter a name for your key and confirm the creation.
4. Once the key is generated, copy it.

### Step 2: Set Your API Key as an Environment Variable
Run the following command in your terminal, replacing `<your-api-key>` with the actual key you copied:
```bash
export DAYTONA_API_KEY="<your-api-key>"
```

This step ensures that OpenHands can authenticate with the Daytona platform when it runs.

### Step 3: Run OpenHands Locally Using Docker
To start the latest version of OpenHands on your machine, execute the following command in your terminal:
```bash
bash -i <(curl -sL https://get.daytona.io/openhands)
```

#### What This Command Does:
- Downloads the latest OpenHands release script.
- Runs the script in an interactive Bash session.
- Automatically pulls and runs the OpenHands container using Docker.

Once executed, OpenHands should be running locally and ready for use.

For more details and manual initialization, view the entire [README.md](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/runtime/impl/daytona/README.md)

## Local Runtime

The Local Runtime allows the OpenHands agent to execute actions directly on your local machine without using Docker. This runtime is primarily intended for controlled environments like CI pipelines or testing scenarios where Docker is not available.

:::caution
**Security Warning**: The Local Runtime runs without any sandbox isolation. The agent can directly access and modify files on your machine. Only use this runtime in controlled environments or when you fully understand the security implications.
:::

### Prerequisites

Before using the Local Runtime, ensure you have the following dependencies installed:

1. You have followed the [Development setup instructions](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).
2. tmux is available on your system.

### Configuration

To use the Local Runtime, besides required configurations like the model, API key, you'll need to set the following options via environment variables or the [config.toml file](https://github.com/All-Hands-AI/OpenHands/blob/main/config.template.toml) when starting OpenHands:

- Via environment variables:

```bash
# Required
export RUNTIME=local

# Optional but recommended
export WORKSPACE_BASE=/path/to/your/workspace
```

- Via `config.toml`:

```toml
[core]
runtime = "local"
workspace_base = "/path/to/your/workspace"
```

If `WORKSPACE_BASE` is not set, the runtime will create a temporary directory for the agent to work in.

### Example Usage

Here's an example of how to start OpenHands with the Local Runtime in Headless Mode:

```bash
# Set the runtime type to local
export RUNTIME=local

# Optionally set a workspace directory
export WORKSPACE_BASE=/path/to/your/project

# Start OpenHands
poetry run python -m openhands.core.main -t "write a bash script that prints hi"
```

### Use Cases

The Local Runtime is particularly useful for:

- CI/CD pipelines where Docker is not available.
- Testing and development of OpenHands itself.
- Environments where container usage is restricted.
- Scenarios where direct file system access is required.
