# Getting Started

## System Requirements
* Docker version 26.0.0+ or Docker Desktop 4.31.0+
* You must be using Linux or Mac OS
  * If you are on Windows, you must use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)

## Installation
The eaisest way to run OpenHands is in Docker. Use `WORKSPACE_BASE` below to
specify which folder the OpenHands agent should modify.

See the [Getting Started](https://docs.all-hands.dev/modules/usage/getting-started) guide for
system requirements and more information.

```bash
WORKSPACE_BASE=$(pwd)/workspace

docker run -it --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.9.1-nikolaik \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/all-hands-ai/openhands:0.9
```

> [!NOTE]
> This command pulls the `0.9` tag, which represents the most recent stable release of OpenHands. You have other options as well:
> - For a specific release version, use `ghcr.io/all-hands-ai/openhands:<OpenHands_version>` (replace <OpenHands_version> with the desired version number).
> - For the most up-to-date development version, use `ghcr.io/all-hands-ai/openhands:main`. This version may be **(unstable!)** and is recommended for testing or development purposes only.
>
> Choose the tag that best suits your needs based on stability requirements and desired features.

You'll find OpenHands running at [http://localhost:3000](http://localhost:3000) with access to `./workspace`. To have OpenHands operate on your code, place it in `./workspace`.
OpenHands will only have access to this workspace folder. The rest of your system will not be affected as it runs in a secured docker sandbox.

Upon opening OpenHands, you must select the appropriate `Model` and enter the `API Key` within the settings that should pop up automatically. These can be set at any time by selecting
the `Settings` button (gear icon) in the UI. If the required `Model` does not exist in the list, you can manually enter it in the text box.

For the development workflow, see [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

Are you having trouble? Check out our [Troubleshooting Guide](https://docs.all-hands.dev/modules/usage/troubleshooting).
