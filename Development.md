# Development Guide
This guide is for people working on OpenHands and editing the source code.
If you wish to contribute your changes, check out the [CONTRIBUTING.md](https://github.com/All-Hands-AI/OpenHands/blob/main/CONTRIBUTING.md) on how to clone and setup the project initially before moving on.
Otherwise, you can clone the OpenHands project directly.

## Start the server for development
### 1. Requirements
* Linux, Mac OS, or [WSL on Windows](https://learn.microsoft.com/en-us/windows/wsl/install)  [ Ubuntu <= 22.04]
* [Docker](https://docs.docker.com/engine/install/) (For those on MacOS, make sure to allow the default Docker socket to be used from advanced settings!)
* [Python](https://www.python.org/downloads/) = 3.11
* [NodeJS](https://nodejs.org/en/download/package-manager) >= 18.17.1
* [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) >= 1.8
* netcat => sudo apt-get install netcat

Make sure you have all these dependencies installed before moving on to `make build`.

#### Develop without sudo access
If you want to develop without system admin/sudo access to upgrade/install `Python` and/or `NodeJs`, you can use `conda` or `mamba` to manage the packages for you:

```bash
# Download and install Mamba (a faster version of conda)
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh

# Install Python 3.11, nodejs, and poetry
mamba install python=3.11
mamba install conda-forge::nodejs
mamba install conda-forge::poetry
```

### 2. Build and Setup The Environment
Begin by building the project which includes setting up the environment and installing dependencies. This step ensures that OpenHands is ready to run on your system:

```bash
make build
```

### 3. Configuring the Language Model
OpenHands supports a diverse array of Language Models (LMs) through the powerful [litellm](https://docs.litellm.ai) library. By default, we've chosen the mighty GPT-4 from OpenAI as our go-to model, but the world is your oyster! You can unleash the potential of Anthropic's suave Claude, the enigmatic Llama, or any other LM that piques your interest.

To configure the LM of your choice, run:

   ```bash
   make setup-config
   ```

   This command will prompt you to enter the LLM API key, model name, and other variables ensuring that OpenHands is tailored to your specific needs. Note that the model name will apply only when you run headless. If you use the UI, please set the model in the UI.

   Note: If you have previously run OpenHands using the docker command, you may have already set some environmental variables in your terminal. The final configurations are set from highest to lowest priority:
   Environment variables > config.toml variables > default variables

**Note on Alternative Models:**
Some alternative models may prove more challenging to tame than others. Fear not, brave adventurer! We shall soon unveil LLM-specific documentation to guide you on your quest.
And if you've already mastered the art of wielding a model other than OpenAI's GPT, we encourage you to share your setup instructions with us by creating instructions and adding it [to our documentation](https://github.com/All-Hands-AI/OpenHands/tree/main/docs/modules/usage/llms).

For a full list of the LM providers and models available, please consult the [litellm documentation](https://docs.litellm.ai/docs/providers).

### 4. Running the application
#### Option A: Run the Full Application
Once the setup is complete, launching OpenHands is as simple as running a single command. This command starts both the backend and frontend servers seamlessly, allowing you to interact with OpenHands:
```bash
make run
```

#### Option B: Individual Server Startup
- **Start the Backend Server:** If you prefer, you can start the backend server independently to focus on backend-related tasks or configurations.
    ```bash
    make start-backend
    ```

- **Start the Frontend Server:** Similarly, you can start the frontend server on its own to work on frontend-related components or interface enhancements.
    ```bash
    make start-frontend
    ```

### 6. LLM Debugging
If you encounter any issues with the Language Model (LM) or you're simply curious, you can inspect the actual LLM prompts and responses. To do so, export DEBUG=1 in the environment and restart the backend.
OpenHands will then log the prompts and responses in the logs/llm/CURRENT_DATE directory, allowing you to identify the causes.

### 7. Help
Need assistance or information on available targets and commands? The help command provides all the necessary guidance to ensure a smooth experience with OpenHands.
```bash
make help
 ```

### 8. Testing
To run tests, refer to the following:
#### Unit tests

```bash
poetry run pytest ./tests/unit/test_*.py
```

#### Integration tests
Please refer to [this README](./tests/integration/README.md) for details.

### 9. Add or update dependency
1. Add your dependency in `pyproject.toml` or use `poetry add xxx`
2. Update the poetry.lock file via `poetry lock --no-update`

## Develop inside Docker container

TL;DR

```bash
make docker-dev
```

See more details [here](./containers/dev/README.md)

If you are just interested in running `OpenHands` without installing all the required tools on your host.

```bash
make docker-run
```

If you do not have `make` on your host, run:

```bash
cd ./containers/dev
./dev.sh
```

You do need [Docker](https://docs.docker.com/engine/install/) installed on your host though.
