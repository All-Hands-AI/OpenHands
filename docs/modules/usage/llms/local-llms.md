# Local LLM with Ollama

:::warning
When using a Local LLM, OpenHands may have limited functionality.
:::

Ensure that you have the Ollama server up and running.
For detailed startup instructions, refer to [here](https://github.com/ollama/ollama).

This guide assumes you've started ollama with `ollama serve`. If you're running ollama differently (e.g. inside docker), the instructions might need to be modified. Please note that if you're running WSL the default ollama configuration blocks requests from docker containers. See [here](#configuring-ollama-service-wsl-en).

## Pull Models

Ollama model names can be found [here](https://ollama.com/library). For a small example, you can use
the `codellama:7b` model. Bigger models will generally perform better.

```bash
ollama pull codellama:7b
```

you can check which models you have downloaded like this:

```bash
~$ ollama list
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## Start OpenHands

### Docker

Use the instructions [here](../getting-started) to start OpenHands using Docker.
But when running `docker run`, you'll need to add a few more arguments:

```bash
--add-host host.docker.internal:host-gateway \
-e LLM_API_KEY="ollama" \
-e LLM_BASE_URL="http://host.docker.internal:11434" \
-e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
```

LLM_OLLAMA_BASE_URL is optional. If you set it, it will be used to show the available installed models in the UI.

Example:

```bash
# The directory you want OpenHands to modify. MUST be an absolute path!
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -it \
    --pull=always \
    --add-host host.docker.internal:host-gateway \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_API_KEY="ollama" \
    -e LLM_BASE_URL="http://host.docker.internal:11434" \
    -e LLM_OLLAMA_BASE_URL="http://host.docker.internal:11434" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/all-hands-ai/openhands:main
```

You should now be able to connect to `http://localhost:3000/`

### Build from Source

Use the instructions in [Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) to build OpenHands.
Make sure `config.toml` is there by running `make setup-config` which will create one for you. In `config.toml`, enter the followings:

```
[core]
workspace_base="./workspace"

[llm]
model="ollama/codellama:7b"
api_key="ollama"
embedding_model="local"
base_url="http://localhost:11434"
ollama_base_url="http://localhost:11434"

```

Replace `LLM_MODEL` of your choice if you need to.

Done! Now you can start OpenHands by: `make run` without Docker. You now should be able to connect to `http://localhost:3000/`

## Select your Model

In the OpenHands UI, click on the Settings wheel in the bottom-left corner.
Then in the `Model` input, enter `ollama/codellama:7b`, or the name of the model you pulled earlier.
If it doesn’t show up in a dropdown, that’s fine, just type it in. Click Save when you’re done.

And now you're ready to go!

## Configuring the ollama service (WSL) {#configuring-ollama-service-wsl-en}

The default configuration for ollama in WSL only serves localhost. This means you can't reach it from a docker container. eg. it wont work with OpenHands. First let's test that ollama is running correctly.

```bash
ollama list # get list of installed models
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #the tag is optional if there is only one
```

Once that is done, test that it allows "outside" requests, like those from inside a docker container.

```bash
docker ps # get list of running docker containers, for most accurate test choose the OpenHands sandbox container.
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#ex. docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

## Fixing it

Now let's make it work. Edit /etc/systemd/system/ollama.service with sudo privileges. (Path may vary depending on linux flavor)

```bash
sudo vi /etc/systemd/system/ollama.service
```

or

```bash
sudo nano /etc/systemd/system/ollama.service
```

In the [Service] bracket add these lines

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

Then save, reload the configuration and restart the service.

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Finally test that ollama is accessible from within the container

```bash
ollama list # get list of installed models
docker ps # get list of running docker containers, for most accurate test choose the OpenHands sandbox container.
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```


# Local LLM with LM Studio

Steps to set up LM Studio:
1. Open LM Studio
2. Go to the Local Server tab.
3. Click the "Start Server" button.
4. Select the model you want to use from the dropdown.


Set the following configs:
```bash
LLM_MODEL="openai/lmstudio"
LLM_BASE_URL="http://localhost:1234/v1"
CUSTOM_LLM_PROVIDER="openai"
```

### Docker

```bash
docker run \
    -it \
    --pull=always \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_MODEL="openai/lmstudio" \
    -e LLM_BASE_URL="http://host.docker.internal:1234/v1" \
    -e CUSTOM_LLM_PROVIDER="openai" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/all-hands-ai/openhands:main
```

You should now be able to connect to `http://localhost:3000/`

In the development environment, you can set the following configs in the `config.toml` file:

```
[core]
workspace_base="./workspace"

[llm]
model="openai/lmstudio"
base_url="http://localhost:1234/v1"
custom_llm_provider="openai"
```

Done! Now you can start OpenHands by: `make run` without Docker. You now should be able to connect to `http://localhost:3000/`

# Note

For WSL, run the following commands in cmd to set up the networking mode to mirrored:

```
python -c  "print('[wsl2]\nnetworkingMode=mirrored',file=open(r'%UserProfile%\.wslconfig','w'))"
wsl --shutdown
```
