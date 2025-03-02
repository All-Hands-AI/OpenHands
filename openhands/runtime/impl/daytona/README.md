# Daytona Runtime

[Daytona](https://www.daytona.io/) is a platform that provides a secure and elastic infrastructure for running AI-generated code. It provides all the necessary features for an AI Agent to interact with a codebase. It provides a Daytona SDK with official Python and TypeScript interfaces for interacting with Daytona, enabling you to programmatically manage development environments and execute code.

## Quick start

Get your Daytona API key from https://app.daytona.io/dashboard/keys and export it:

```bash
export DAYTONA_API_KEY="<your-api-key>"
```

Use the following command to run the latest OpenHands release locally using Docker:

```bash
bash -i <(curl -sL https://get.daytona.io/openhands)
```


## Getting started

1. Sign in at https://app.daytona.io/

1. Generate and copy your API key

1. Set the `OPENHANDS_VERSION` environment variable to the latest release's version seen in the main README.md file; as well as the `DAYTONA_API_KEY`

```bash
export OPENHANDS_VERSION=<OPENHANDS_RELEASE>  # e.g. 0.27
export DAYTONA_API_KEY=<your_api_key>
```

1. Run the following `docker` command:

```bash
docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:${OPENHANDS_VERSION}-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -e RUNTIME=daytona \
    -e DAYTONA_API_KEY=${DAYTONA_API_KEY} \
    -v ~/.openhands-state:/.openhands-state \
    -p 3000:3000 \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:${OPENHANDS_VERSION}
```
> **Tip:** If you don't want your sandboxes to default to the US region, you can set the `DAYTONA_TARGET` environment variable to `eu`

Alternatively, if you want to run the OpenHands app on your local machine using `make run` without Docker, set the following environment variables first:

```bash
export RUNTIME="daytona"
export DAYTONA_API_KEY="<your-api-key>"
```

## Documentation
Read more by visiting our [documentation](https://www.daytona.io/docs/) page.
