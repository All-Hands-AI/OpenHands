# Local LLM with SGLang or vLLM

:::warning
When using a Local LLM, OpenHands may have limited functionality.
It is highly recommended that you use GPUs to serve local models for optimal experience.
:::


## News

- 2025/03/31: We released an open model OpenHands LM v0.1 32B that achieves 37.1% on SWE-Bench Verified ([blog](https://www.all-hands.dev/blog/introducing-openhands-lm-32b----a-strong-open-coding-agent-model), [model](https://huggingface.co/all-hands/openhands-lm-32b-v0.1)).


## Download the Model from Huggingface

For example, to download [OpenHands LM 32B v0.1](https://huggingface.co/all-hands/openhands-lm-32b-v0.1):

```bash
huggingface-cli download all-hands/openhands-lm-32b-v0.1 --local-dir my_folder/openhands-lm-32b-v0.1
```

## Create an OpenAI-Compatible Endpoint With a Model Serving Framework

### Serving with SGLang

- Install SGLang following the official documentation: https://docs.sglang.ai/start/install.html
- Example launch command for OpenHands LM 32B (with at least 2 GPUs):

```bash
SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 python3 -m sglang.launch_server \
    --model my_folder/openhands-lm-32b-v0.1 \
    --served-model-name openhands-lm-32b-v0.1 \
    --port 8000 \
    --tp 2 --dp 1 \
    --host 0.0.0.0 \
    --api-key mykey --context-length 131072
```

### Serving with vLLM

- Install vLLM following the official documentation: https://docs.vllm.ai/en/latest/getting_started/installation.html
- Example launch command for OpenHands LM 32B (with at least 2 GPUs):

```bash
vllm serve my_folder/openhands-lm-32b-v0.1 \
    --host 0.0.0.0 --port 8000 \
    --api-key mykey \
    --tensor-parallel-size 2 \
    --served-model-name openhands-lm-32b-v0.1
    --enable-prefix-caching
```

### Configure OpenHands Application

When running `openhands`, you'll need to set the following in the OpenHands UI through the Settings:
- the model to `openai/openhands-lm-32b-v0.1` (`openai/`, and then `served-model-name` you set above)
- the base url to `http://host.docker.internal:8000`
- the API key is optional, you can use any string, such as `mykey` you set above.


## Run OpenHands in Development Mode

### Build from Source

Use the instructions in [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) to build OpenHands.
Make sure `config.toml` is there by running `make setup-config` which will create one for you. In `config.toml`, enter the followings:

```
[core]
workspace_base="./workspace"

[llm]
embedding_model="local"
ollama_base_url="http://localhost:8000"

```

Done! Now you can start OpenHands by: `make run`. You now should be able to connect to `http://localhost:3000/`

### Configure the Web Application

In the OpenHands UI, click on the Settings wheel in the bottom-left corner.
Then in the `Model` input, enter `openai/openhands-lm-32b-v0.1`, or the name of the model you pulled earlier.
If it doesn’t show up in the dropdown, enable `Advanced Settings` and type it in.

In the API Key field, enter `my` or any value you setted.

In the Base URL field, enter `http://host.docker.internal:8000`.

And now you're ready to go!
