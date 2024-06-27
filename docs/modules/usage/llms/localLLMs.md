# Local LLM with Ollama

## Prerequisites

Ensure that you have the Ollama server up and running. For detailed startup instructions, refer to the [Ollama GitHub repository](https://github.com/ollama/ollama).

> **Note**: This guide assumes you've started Ollama with `ollama serve`. If you're running Ollama differently (e.g., inside Docker), the instructions might need to be modified.
>
> **Important**: If you're running WSL, the default Ollama configuration blocks requests from Docker containers. See [Configuring Ollama Service (WSL)](#configuring-ollama-service-wsl) for more information.

## Pull Models

Ollama model names can be found in the [Ollama Library](https://ollama.com/library). For a small example, you can use the `codellama:7b` model. Larger models generally perform better.

```bash
ollama pull codellama:7b
```

To check which models you have downloaded:

```bash
ollama list
```

Example output:
```
NAME                            ID              SIZE    MODIFIED
codellama:7b                    8fdf8f752f6e    3.8 GB  6 weeks ago
mistral:7b-instruct-v0.2-q4_K_M eb14864c7427    4.4 GB  2 weeks ago
starcoder2:latest               f67ae0f64584    1.7 GB  19 hours ago
```

## Start OpenDevin

### Using Docker

Follow the instructions [here](../intro) to start OpenDevin using Docker, but add these additional arguments when running `docker run`:

```bash
--add-host host.docker.internal:host-gateway \
-e LLM_API_KEY="ollama" \
-e LLM_BASE_URL="http://host.docker.internal:11434" \
```

Full example:

```bash
# Set the directory you want OpenDevin to modify (MUST be an absolute path)
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    -it \
    --pull=always \
    --add-host host.docker.internal:host-gateway \
    -e SANDBOX_USER_ID=$(id -u) \
    -e LLM_API_KEY="ollama" \
    -e LLM_BASE_URL="http://host.docker.internal:11434" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/opendevin/opendevin:main
```

After running this command, you should be able to connect to `http://localhost:3000/`.

### Building from Source

1. Follow the instructions in [Development.md](https://github.com/OpenDevin/OpenDevin/blob/main/Development.md) to build OpenDevin.
2. Run `make setup-config` to create a `config.toml` file.
3. Edit `config.toml` with the following settings:

```toml
LLM_MODEL="ollama/codellama:7b"
LLM_API_KEY="ollama"
LLM_EMBEDDING_MODEL="local"
LLM_BASE_URL="http://localhost:11434"
WORKSPACE_BASE="./workspace"
WORKSPACE_DIR="$(pwd)/workspace"
```

> **Note**: Replace `LLM_MODEL` with your preferred model if needed.

4. Start Devin by running `make run` (without Docker).
5. Connect to `http://localhost:3000/`.

## Select your Model

1. In the OpenDevin UI, click on the Settings wheel in the bottom-left corner.
2. In the `Model` input, enter `ollama/codellama:7b`, or the name of the model you pulled earlier.
   - If it doesn't appear in a dropdown, type it in manually.
3. Click Save when you're done.

You're now ready to use OpenDevin with your local LLM!

## Configuring Ollama Service (WSL) {#configuring-ollama-service-wsl}

The default configuration for Ollama in WSL only serves localhost, which means it can't be reached from a Docker container. Follow these steps to configure Ollama for use with OpenDevin:

1. Test that Ollama is running correctly:

```bash
ollama list  # Get list of installed models
curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
```

2. Test if it allows "outside" requests (e.g., from inside a Docker container):

```bash
docker ps  # Get list of running Docker containers
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

### Fixing the Configuration

1. Edit `/etc/systemd/system/ollama.service` with sudo privileges:

```bash
sudo nano /etc/systemd/system/ollama.service
```

2. In the `[Service]` section, add these lines:

```
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
```

3. Save the file, then reload the configuration and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

4. Test that Ollama is now accessible from within the container:

```bash
ollama list  # Get list of installed models
docker ps  # Get list of running Docker containers
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

If successful, you should now be able to use OpenDevin with your local Ollama LLM setup.