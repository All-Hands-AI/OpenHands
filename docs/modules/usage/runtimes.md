# Runtime Configuration

A Runtime is an environment where the OpenHands agent can edit files and run
commands.

By default, OpenHands uses a Docker-based runtime, running on your local computer.
But this can be tricky to set up and manage, so we also offer support for "remote" runtimes.
In these cases, you'll generally need to set up an account with a runtime provider
and get an API key to use their runtime.

## Docker Runtime
This is the default Runtime that's used when you start OpenHands. You might notice
some flags being passed to `docker run` that make this possible:

```
docker run # ...
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.11-nikolaik \
    -v /var/run/docker.sock:/var/run/docker.sock \
    # ...
```

The `SANDBOX_RUNTIME_CONTAINER_IMAGE` from nikolaik is a pre-built runtime image
that contains our Runtime server, as well as some basic utilities for Python and NodeJS.
You can also [build your own runtime image](how-to/custom-sandbox-guide).

### Connecting to your filesystem
One useful feature here is the ability to connect to your local filesystem.
This functionality can be tricky, so we don't recommend it by default. But
it allows OpenHands to work directly on files on your computer.

To mount your filesystem into the runtime, add the following options to
the `docker run` command:

```bash
export WORKSPACE_BASE=/path/to/your/code

docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    # ...
```

Note that this can cause some issues with file permissions (hence the `SANDBOX_USER_ID` variable)
but seems to work well on most systems.


## All Hands Runtime
The All Hands Runtime is currently in beta. You can request access by joining
the  #remote-runtime-limited-beta channel on Slack (see the README for an invite).

To use the All Hands Runtime, set the following environment variables when
starting OpenHands:

```bash
docker run # ...
    -e RUNTIME=remote \
    -e SANDBOX_REMOTE_RUNTIME_API_URL="https://runtime.app.all-hands.dev" \
    -e SANDBOX_API_KEY="your-api-key" \
    -e SANDBOX_KEEP_REMOTE_RUNTIME_ALIVE="true" \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.11-nikolaik \
    # ...
```

## Modal Runtime
Our partners at [Modal](https://modal.com/) have also provided a runtime for OpenHands.

To use the Modal Runtime, create an account, and then [create an API key](https://modal.com/settings)

You'll then need to set the following environment variables when starting OpenHands:
```bash
docker run # ...
    -e RUNTIME=modal \
    -e MODAL_API_TOKEN_ID="your-id" \
    -e MODAL_API_TOKEN_SECRET="your-secret" \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.11-nikolaik \
```
