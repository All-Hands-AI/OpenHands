# How to build custom Docker sandbox for OpenHands

[Docker](https://docs.docker.com/get-started/docker-overview/) is an open platform for developing, shipping, and running applications.

This folder contains working examples to get you started.

## Build the sandbox

```bash
# rename the files and make changes as you please
cp build.example.sh build.sh
cp compose.example.yml compose.yml

./build.sh <my base image>
```

## Start up sandbox

```bash
docker compose up -d
```

## Update config.toml and restart OpenHands

```toml
[core]
runtime="docker"

[sandbox]
container_name="<sandbox container_name>"
remote_runtime_api_url="http://<host>:<published sandbox port>/"

```
