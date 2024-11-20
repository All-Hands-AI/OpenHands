# How to build custom Docker sandbox for OpenHands

If you are looking for instructions for building custom sandboxes managed by OpenHands. Please follow [here](https://docs.all-hands.dev/modules/usage/how-to/custom-sandbox-guide)

This folder contains working examples for building a custom sandbox that you can run in the same Docker context or a different one. See Docker [context](https://docs.docker.com/engine/manage-resources/contexts/) for more info.

## Build the sandbox

Before attempting to build the sandbox, make sure you can [build OpenHands](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md).

You may try and build inside docker container.

```bash
make docker-dev
```

```bash
# rename the files and make changes as you please
cp build.example.sh build.sh
cp compose.example.yml compose.yml

# ./build.sh <my base image> <my tag>
./build.sh
```

## Start up sandbox

```bash
docker compose up -d
```

## Start OpenHands

Update config.toml

```toml
[core]

[sandbox]
# http://<host>:<published sandbox port>/
remote_runtime_api_url = "http://host.docker.internal:8000/"
# <sandbox container_name>
container_name = "custom-sandbox"
# docker context endpoint
docker_endpoint = "unix:///var/run/docker.sock"
```

or use env.

```bash
export SANDBOX_REMOTE_RUNTIME_API_URL=http://host.docker.internal:8000/
export SANDBOX_CONTAINER_NAME=custom-sandbox
export SANDBOX_DOCKER_ENDPOINT=unix:///var/run/docker.sock
```

```bash
make docker-run
```
