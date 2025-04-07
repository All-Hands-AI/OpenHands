# Custom Sandbox

The sandbox is where the agent performs its tasks. Instead of running commands directly on your computer
(which could be risky), the agent runs them inside a Docker container.

The default OpenHands sandbox (`python-nodejs:python3.12-nodejs22`
from [nikolaik/python-nodejs](https://hub.docker.com/r/nikolaik/python-nodejs)) comes with some packages installed such
as python and Node.js but may need other software installed by default.

You have two options for customization:

- Use an existing image with the required software.
- Create your own custom Docker image.

If you choose the first option, you can skip the `Create Your Docker Image` section.

## Create Your Docker Image

To create a custom Docker image, it must be Debian based.

For example, if you want OpenHands to have `ruby` installed, you could create a `Dockerfile` with the following content:

```dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# Install required packages
RUN apt-get update && apt-get install -y ruby
```

Or you could use a Ruby-specific base image:

```dockerfile
FROM ruby:latest
```

Save this file in a folder. Then, build your Docker image (e.g., named custom-image) by navigating to the folder in
the terminal and running::
```bash
docker build -t custom-image .
```

This will produce a new image called `custom-image`, which will be available in Docker.

## Using the Docker Command

When running OpenHands using [the docker command](/modules/usage/installation#start-the-app), replace
`-e SANDBOX_RUNTIME_CONTAINER_IMAGE=...` with `-e SANDBOX_BASE_CONTAINER_IMAGE=<custom image name>`:

```commandline
docker run -it --rm --pull=always \
    -e SANDBOX_BASE_CONTAINER_IMAGE=custom-image \
    ...
```

## Using the Development Workflow

### Setup

First, ensure you can run OpenHands by following the instructions in [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

### Specify the Base Sandbox Image

In the `config.toml` file within the OpenHands directory, set the `sandbox_base_container_image` to the image you want to use.
This can be an image you’ve already pulled or one you’ve built:

```bash
[core]
...
sandbox_base_container_image="custom-image"
```

### Additional Configuration Options

The `config.toml` file supports several other options for customizing your sandbox:

```toml
[core]
# Install additional dependencies when the runtime is built
# Can contain any valid shell commands
# If you need the path to the Python interpreter in any of these commands, you can use the $OH_INTERPRETER_PATH variable
runtime_extra_deps = """
pip install numpy pandas
apt-get update && apt-get install -y ffmpeg
"""

# Set environment variables for the runtime
# Useful for configuration that needs to be available at runtime
runtime_startup_env_vars = { DATABASE_URL = "postgresql://user:pass@localhost/db" }

# Specify platform for multi-architecture builds (e.g., "linux/amd64" or "linux/arm64")
platform = "linux/amd64"
```

### Run

Run OpenHands by running ```make run``` in the top level directory.
