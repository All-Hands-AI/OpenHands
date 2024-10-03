# Custom Sandbox

The sandbox is where the agent does its work. Instead of running commands directly on your computer
(which could be dangerous), the agent runs them inside of a Docker container.

The default OpenHands sandbox (`python-nodejs:python3.12-nodejs22`
from [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) comes with some packages installed such
as python and Node.js but your use case may need additional software installed by default.

There are two ways you can do so:

1. Use an existing image from docker hub.
2. Creating your own custom docker image and using it.

If you want to take the first approach, you can skip the `Create Your Docker Image` section.

## Setup

Make sure you are able to run OpenHands using the [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) first.

## Create Your Docker Image

To create a custom docker image, it must be debian/ubuntu based.

For example, if we want OpenHands to have access to the `node` binary, we would use the following Dockerfile:

```dockerfile
# Start with latest ubuntu image
FROM ubuntu:latest

# Run needed updates
RUN apt-get update && apt-get install -y

# Install node
RUN apt-get install -y nodejs
```

Next build your docker image with the name of your choice, for example `custom_image`.

To do this you can create a directory and put your file inside it with the name `Dockerfile`, and inside the directory run the following command:

```bash
docker build -t custom_image .
```

This will produce a new image called ```custom_image``` that will be available in Docker Engine.

> Note that in the configuration described in this document, OpenHands will run as user "openhands" inside the sandbox and thus all packages installed via the docker file should be available to all users on the system, not just root.
>
> Installing with apt-get above installs node for all users.

## Specify your sandbox image in config.toml file

OpenHands configuration occurs via the top-level `config.toml` file.

Create a `config.toml` file in the OpenHands directory and enter these contents:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
sandbox_base_container_image="custom_image"
```

For `sandbox_base_container_image`, you can specify either:

1. The name of your custom image that you built in the previous step (e.g., `”custom_image”`)
2. A pre-existing image from Docker Hub (e.g., `”node:20”` if you want a sandbox with Node.js pre-installed)

## Run
Run OpenHands by running ```make run``` in the top level directory.

Navigate to ```localhost:3001``` and check if your desired dependencies are available.

In the case of the example above, running ```node -v``` in the terminal produces ```v20.15.0```.

Congratulations!

## Technical Explanation

Please refer to [custom docker image section of the runtime documentation](https://docs.all-hands.dev/modules/usage/architecture/runtime#advanced-how-openhands-builds-and-maintains-od-runtime-images) for more details.

## Troubleshooting / Errors

### Error: ```useradd: UID 1000 is not unique```

If you see this error in the console output it is because OpenHands is trying to create the openhands user in the sandbox with a UID of 1000, however this UID is already being used in the image (for some reason). To fix this change the sandbox_user_id field in the config.toml file to a different value:

```toml
[core]
workspace_base="./workspace"
run_as_openhands=true
sandbox_base_container_image="custom_image"
sandbox_user_id="1001"
```

### Port use errors

If you see an error about a port being in use or unavailable, try deleting all running Docker Containers (run `docker ps` and `docker rm` relevant containers) and then re-running ```make run``` .

## Discuss

For other issues or questions join the [Slack](https://join.slack.com/t/opendevin/shared_invite/zt-2oikve2hu-UDxHeo8nsE69y6T7yFX_BA) or [Discord](https://discord.gg/ESHStjSjD4) and ask!
