# Local LLM Guide with Ollama server

Ensure that you have the Ollama server up and running.
For detailed startup instructions, refer to the [here](https://github.com/ollama/ollama)

This guide assumes you've started ollama with `ollama serve`. If you're running ollama differently (e.g. inside docker), the instructions might need to be modified. Please note that if you're running wsl the default ollama configuration blocks requests from docker containers. See [here](#4-configuring-the-ollama-service-wsl).

## 1. Pull Models

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

## 2. Start OpenDevin

Use the instructions in [README.md](/README.md) to start OpenDevin using Docker.
But when running `docker run`, you'll need to add a few more arguments:

```bash
--add-host host.docker.internal=host-gateway \
-e LLM_API_KEY="ollama" \
-e LLM_BASE_URL="http://host.docker.internal:11434" \
```

For example:

```bash
# The directory you want OpenDevin to modify. MUST be an absolute path!
export WORKSPACE_BASE=$(pwd)/workspace

docker run \
    --add-host host.docker.internal=host-gateway \
    -e LLM_API_KEY="ollama" \
    -e LLM_BASE_URL="http://host.docker.internal:11434" \
    -e WORKSPACE_MOUNT_PATH=$WORKSPACE_BASE \
    -v $WORKSPACE_BASE:/opt/workspace_base \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 3000:3000 \
    ghcr.io/opendevin/opendevin:main
```

You should now be able to connect to `http://localhost:3000/`

## 3. Select your Model

In the OpenDevin UI, click on the Settings wheel in the bottom-left corner.
Then in the `Model` input, enter `ollama/codellama:7b`, or the name of the model you pulled earlier.
If it doesn’t show up in a dropdown, that’s fine, just type it in. Click Save when you’re done.

And now you're ready to go!

## 4. Configuring the ollama service (WSL)

The default configuration for ollama in wsl only serves localhost. This means you can't reach it from a docker container. eg. it wont work with OpenDevin. First let's test that ollama is running correctly.

```bash
ollama list # get list of installed models
curl http://localhost:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama:7b","prompt":"hi"}'
#ex. curl http://localhost:11434/api/generate -d '{"model":"codellama","prompt":"hi"}' #the tag is optional if there is only one
```

Once that is done test that it allows "outside" requests, like those from inside a docker container.

```bash
docker ps # get list of running docker containers, for most accurate test choose the open devin sandbox container.
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
#ex. docker exec cd9cc82f7a11 curl http://host.docker.internal:11434/api/generate -d '{"model":"codellama","prompt":"hi"}'
```

### Fixing it

Now let's make it work, edit /etc/systemd/system/ollama.service with sudo priviledges. (Path may vary depending on linux flavor)

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
docker ps # get list of running docker containers, for most accurate test choose the open devin sandbox container.
docker exec [CONTAINER ID] curl http://host.docker.internal:11434/api/generate -d '{"model":"[NAME]","prompt":"hi"}'
```
