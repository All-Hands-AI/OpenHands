# Groq LLM API

## Completion

OpenDevin uses LiteLLM for completion calls. The following resources are relevant for using OpenDevin with Groq LLM API.

- [Groq LLM API](https://docs.litellm.ai/docs/providers/groq)

### Setup

To use Groq LLM API with OpenDevin, you'll need to set the following environment variables using `-e`:

```
-e GROQ_API_KEY="your_api_key"
-e LLM_MODEL="groq/llama3-70b-8192"
```

- You can choose [model type](https://docs.litellm.ai/docs/providers/groq#supported-models---all-groq-models-supported).

- Best to check [groq's official documentation website](https://console.groq.com/docs/models) for more model type information.

### Example command

```
export WORKSPACE_BASE=./workspace

docker run \
    -e GROQ_API_KEY="your_api_key" \
    -e LLM_MODEL="groq/llama3-70b-8192" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    --add-host host.docker.internal=host-gateway \
    ghcr.io/opendevin/opendevin:0.4.0
```
