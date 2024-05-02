# Development Guide
This guide is for people working on OpenDevin and editing the source code.

## Start the server for development

### 1. Requirements
* Linux, Mac OS, or [WSL on Windows](https://learn.microsoft.com/en-us/windows/wsl/install)
* [Docker](https://docs.docker.com/engine/install/)(For those on MacOS, make sure to allow the default Docker socket to be used from advanced settings!)
* [Python](https://www.python.org/downloads/) >= 3.11
* [NodeJS](https://nodejs.org/en/download/package-manager) >= 18.17.1
* [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) >= 1.8

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

- **Build the Project:** Begin by building the project, which includes setting up the environment and installing dependencies. This step ensures that OpenDevin is ready to run smoothly on your system.
    ```bash
    make build
    ```

### 3. Configuring the Language Model

OpenDevin supports a diverse array of Language Models (LMs) through the powerful [litellm](https://docs.litellm.ai) library. By default, we've chosen the mighty GPT-4 from OpenAI as our go-to model, but the world is your oyster! You can unleash the potential of Anthropic's suave Claude, the enigmatic Llama, or any other LM that piques your interest.

To configure the LM of your choice, follow these steps:

1. **Using the Makefile: The Effortless Approach**
   With a single command, you can have a smooth LM setup for your OpenDevin experience. Simply run:
   ```bash
   make setup-config
   ```
   This command will prompt you to enter the LLM API key, model name, and other variables ensuring that OpenDevin is tailored to your specific needs. Note that the model name will apply only when you run headless. If you use the UI, please set the model in the UI.

**Note on Alternative Models:**
Some alternative models may prove more challenging to tame than others. Fear not, brave adventurer! We shall soon unveil LLM-specific documentation to guide you on your quest. And if you've already mastered the art of wielding a model other than OpenAI's GPT, we encourage you to [share your setup instructions with us](https://github.com/OpenDevin/OpenDevin/issues/417).

For a full list of the LM providers and models available, please consult the [litellm documentation](https://docs.litellm.ai/docs/providers).

There is also [documentation for running with local models using ollama](./docs/documentation/LOCAL_LLM_GUIDE.md).

### 4. Run the Application

- **Run the Application:** Once the setup is complete, launching OpenDevin is as simple as running a single command. This command starts both the backend and frontend servers seamlessly, allowing you to interact with OpenDevin without any hassle.
    ```bash
    make run
    ```

### 5. Individual Server Startup

- **Start the Backend Server:** If you prefer, you can start the backend server independently to focus on backend-related tasks or configurations.
    ```bash
    make start-backend
    ```

- **Start the Frontend Server:** Similarly, you can start the frontend server on its own to work on frontend-related components or interface enhancements.
    ```bash
    make start-frontend
    ```

### 6. LLM Debugging

If you encounter any issues with the Language Model (LM) or you're simply curious, you can inspect the actual LLM prompts and responses. To do so, export DEBUG=1 in the environment and restart the backend. OpenDevin will then log the prompts and responses in the logs/llm/CURRENT_DATE directory, allowing you to identify the causes.

### 7. Help

- **Get Some Help:** Need assistance or information on available targets and commands? The help command provides all the necessary guidance to ensure a smooth experience with OpenDevin.
    ```bash
    make help
    ```

### 8. Testing

#### Unit tests

```bash
poetry run pytest ./tests/unit/test_sandbox.py
```

#### Integration tests

Please refer to [this README](./tests/integration/README.md) for details.
