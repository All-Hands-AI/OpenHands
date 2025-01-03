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

For example, if you want OpenHands to have `ruby` installed, create a `Dockerfile` with the following content:

```dockerfile
FROM debian:latest

# Install required packages
RUN apt-get update && apt-get install -y ruby
```

Save this file in a folder. Then, build your Docker image (e.g., named custom-image) by navigating to the folder in
the terminal and running::
```bash
docker build -t custom-image .
```

This will produce a new image called `custom-image`, which will be available in Docker.

> Note that in the configuration described in this document, OpenHands will run as user "openhands" inside the
> sandbox and thus all packages installed via the docker file should be available to all users on the system, not just root.

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

### Run

Run OpenHands by running ```make run``` in the top level directory.
