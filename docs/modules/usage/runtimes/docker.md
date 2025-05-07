# Docker Runtime

This is the default Runtime that's used when you start OpenHands.

## Image
The `SANDBOX_RUNTIME_CONTAINER_IMAGE` from nikolaik is a pre-built runtime image
that contains our Runtime server, as well as some basic utilities for Python and NodeJS.
You can also [build your own runtime image](../how-to/custom-sandbox-guide).

## Connecting to Your filesystem
A useful feature is the ability to connect to your local filesystem. To mount your filesystem into the runtime:

### Using SANDBOX_VOLUMES

The simplest way to mount your local filesystem is to use the `SANDBOX_VOLUMES` environment variable:

```bash
docker run # ...
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_VOLUMES=/path/to/your/code:/workspace:rw \
    # ...
```

The `SANDBOX_VOLUMES` format is `host_path:container_path[:mode]` where:

- `host_path`: The path on your host machine that you want to mount.
- `container_path`: The path inside the container where the host path will be mounted.
  - Use `/workspace` for files you want the agent to modify. The agent works in `/workspace` by default.
  - Use a different path (e.g., `/data`) for read-only reference materials or large datasets.
- `mode`: Optional mount mode, either `rw` (read-write, default) or `ro` (read-only).

You can also specify multiple mounts by separating them with commas (`,`):

```bash
-e SANDBOX_VOLUMES=/path1:/workspace/path1,/path2:/workspace/path2:ro
```

Examples:

```bash
# Linux and Mac Example - Writable workspace
-e SANDBOX_VOLUMES=$HOME/OpenHands:/workspace:rw

# WSL on Windows Example - Writable workspace
-e SANDBOX_VOLUMES=/mnt/c/dev/OpenHands:/workspace:rw

# Read-only reference code example
-e SANDBOX_VOLUMES=/path/to/reference/code:/data:ro

# Multiple mounts example - Writable workspace with read-only reference data
-e SANDBOX_VOLUMES=$HOME/projects:/workspace:rw,/path/to/large/dataset:/data:ro
```

### Using WORKSPACE_* variables (Deprecated)

> **Note:** This method is deprecated and will be removed in a future version. Please use `SANDBOX_VOLUMES` instead.

1. Set `WORKSPACE_BASE`:

    ```bash
    export WORKSPACE_BASE=/path/to/your/code
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

The `-e SANDBOX_USER_ID=$(id -u)` is passed to the Docker command to ensure the sandbox user matches the host user’s
permissions. This prevents the agent from creating root-owned files in the mounted workspace.

## Hardened Docker Installation

When deploying OpenHands in environments where security is a priority, you should consider implementing a hardened
Docker configuration. This section provides recommendations for securing your OpenHands Docker deployment beyond the default configuration.

### Security Considerations

The default Docker configuration in the README is designed for ease of use on a local development machine. If you're
running on a public network (e.g. airport WiFi), you should implement additional security measures.

### Network Binding Security

By default, OpenHands binds to all network interfaces (`0.0.0.0`), which can expose your instance to all networks the
host is connected to. For a more secure setup:

1. **Restrict Network Binding**: Use the `runtime_binding_address` configuration to restrict which network interfaces OpenHands listens on:

   ```bash
   docker run # ...
       -e SANDBOX_RUNTIME_BINDING_ADDRESS=127.0.0.1 \
       # ...
   ```

   This configuration ensures OpenHands only listens on the loopback interface (`127.0.0.1`), making it accessible only from the local machine.

2. **Secure Port Binding**: Modify the `-p` flag to bind only to localhost instead of all interfaces:

   ```bash
   docker run # ... \
       -p 127.0.0.1:3000:3000 \
   ```

   This ensures that the OpenHands web interface is only accessible from the local machine, not from other machines on the network.

### Network Isolation

Use Docker's network features to isolate OpenHands:

```bash
# Create an isolated network
docker network create openhands-network

# Run OpenHands in the isolated network
docker run # ... \
    --network openhands-network \
```
