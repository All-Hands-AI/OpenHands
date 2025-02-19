# Runtime Configuration

A Runtime is an environment where the OpenHands agent can edit files and run
commands.

By default, OpenHands uses a Docker-based runtime, running on your local computer.
This means you only have to pay for the LLM you're using, and your code is only ever sent to the LLM.

We also support "remote" runtimes, which are typically managed by third-parties.
They can make setup a bit simpler and more scalable, especially
if you're running many OpenHands conversations in parallel (e.g. to do evaluation).

## Docker Runtime
This is the default Runtime that's used when you start OpenHands. You might notice
some flags being passed to `docker run` that make this possible:

```
docker run # ...
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.25-nikolaik \
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

## All Hands Runtime
The All Hands Runtime is currently in beta. You can request access by joining
the #remote-runtime-limited-beta channel on Slack ([see the README](https://github.com/All-Hands-AI/OpenHands?tab=readme-ov-file#-how-to-join-the-community) for an invite).

To use the All Hands Runtime, set the following environment variables when
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
