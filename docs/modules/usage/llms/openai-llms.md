# OpenAI

OpenHands uses [LiteLLM](https://www.litellm.ai/) to make calls to OpenAI's chat models. You can find their full documentation on OpenAI chat calls [here](https://docs.litellm.ai/docs/providers/openai).

## Configuration

### Manual Configuration

When running the OpenHands Docker image, you'll need to set the following environment variables:

```sh
LLM_MODEL="openai/<gpt-model-name>" # e.g. "openai/gpt-4o"
LLM_API_KEY="<your-openai-project-api-key>"
```

To see a full list of OpenAI models that LiteLLM supports, please visit https://docs.litellm.ai/docs/providers/openai#openai-chat-completion-models.

To find or create your OpenAI Project API Key, please visit https://platform.openai.com/api-keys.

**Example**:

```sh
export WORKSPACE_BASE=$(pwd)/workspace

docker run -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_MODEL="openai/<gpt-model-name>" \
    -e LLM_API_KEY="<your-openai-project-api-key>" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/opendevin/opendevin:0.8
```

### UI Configuration

You can also directly set the `LLM_MODEL` and `LLM_API_KEY` in the OpenHands client itself. Follow this guide to get up and running with the OpenHands client.

From there, you can set your model and API key in the settings window.

## Using OpenAI-Compatible Endpoints

Just as for OpenAI Chat completions, we use LiteLLM for OpenAI-compatible endpoints. You can find their full documentation on this topic [here](https://docs.litellm.ai/docs/providers/openai_compatible).

When running the OpenHands Docker image, you'll need to set the following environment variables:

```sh
LLM_BASE_URL="<api-base-url>" # e.g. "http://0.0.0.0:3000"
LLM_MODEL="openai/<model-name>" # e.g. "openai/mistral"
LLM_API_KEY="<your-api-key>"
```

**Example**:

```sh
export WORKSPACE_BASE=$(pwd)/workspace

docker run -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -e LLM_BASE_URL="<api-base-url>" \
    -e LLM_MODEL="openai/<model-name>" \
    -e LLM_API_KEY="<your-api-key>" \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app-$(date +%Y%m%d%H%M%S) \
    ghcr.io/opendevin/opendevin:0.8
```
