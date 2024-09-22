SHELL=/bin/bash
# Makefile for OpenHands project

# Variables
BACKEND_HOST ?= "127.0.0.1"
BACKEND_PORT = 3000
BACKEND_HOST_PORT = "$(BACKEND_HOST):$(BACKEND_PORT)"
FRONTEND_PORT = 3001
DEFAULT_WORKSPACE_DIR = "./workspace"
DEFAULT_MODEL = "gpt-4o"
CONFIG_FILE = config.toml
PRE_COMMIT_CONFIG_PATH = "./dev_config/python/.pre-commit-config.yaml"
PYTHON_VERSION = 3.11

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

# Build
build:
	@echo "$(GREEN)Building project...$(RESET)"
	@$(MAKE) -s check-dependencies
	@$(MAKE) -s install-python-dependencies
	@$(MAKE) -s install-frontend-dependencies
	@$(MAKE) -s install-pre-commit-hooks
	@$(MAKE) -s build-frontend
	@echo "$(GREEN)Build completed successfully.$(RESET)"

check-dependencies:
	@echo "$(YELLOW)Checking dependencies...$(RESET)"
	@$(MAKE) -s check-system
	@$(MAKE) -s check-python
	@$(MAKE) -s check-npm
	@$(MAKE) -s check-nodejs
ifeq ($(INSTALL_DOCKER),)
	@$(MAKE) -s check-docker
endif
	@$(MAKE) -s check-poetry
	@echo "$(GREEN)Dependencies checked successfully.$(RESET)"

check-system:
	@echo "$(YELLOW)Checking system...$(RESET)"
	@if [ "$(shell uname)" = "Darwin" ]; then \
		echo "$(BLUE)macOS detected.$(RESET)"; \
	elif [ "$(shell uname)" = "Linux" ]; then \
		if [ -f "/etc/manjaro-release" ]; then \
			echo "$(BLUE)Manjaro Linux detected.$(RESET)"; \
		else \
			echo "$(BLUE)Linux detected.$(RESET)"; \
		fi; \
	elif [ "$$(uname -r | grep -i microsoft)" ]; then \
		echo "$(BLUE)Windows Subsystem for Linux detected.$(RESET)"; \
	else \
		echo "$(RED)Unsupported system detected. Please use macOS, Linux, or Windows Subsystem for Linux (WSL).$(RESET)"; \
		exit 1; \
	fi

check-python:
	@echo "$(YELLOW)Checking Python installation...$(RESET)"
	@if command -v python$(PYTHON_VERSION) > /dev/null; then \
		echo "$(BLUE)$(shell python$(PYTHON_VERSION) --version) is already installed.$(RESET)"; \
	else \
		echo "$(RED)Python $(PYTHON_VERSION) is not installed. Please install Python $(PYTHON_VERSION) to continue.$(RESET)"; \
		exit 1; \
	fi

check-npm:
	@echo "$(YELLOW)Checking npm installation...$(RESET)"
	@if command -v npm > /dev/null; then \
		echo "$(BLUE)npm $(shell npm --version) is already installed.$(RESET)"; \
	else \
		echo "$(RED)npm is not installed. Please install Node.js to continue.$(RESET)"; \
		exit 1; \
	fi

check-nodejs:
	@echo "$(YELLOW)Checking Node.js installation...$(RESET)"
	@if command -v node > /dev/null; then \
		NODE_VERSION=$(shell node --version | sed -E 's/v//g'); \
		IFS='.' read -r -a NODE_VERSION_ARRAY <<< "$$NODE_VERSION"; \
		if [ "$${NODE_VERSION_ARRAY[0]}" -gt 18 ] || ([ "$${NODE_VERSION_ARRAY[0]}" -eq 18 ] && [ "$${NODE_VERSION_ARRAY[1]}" -gt 17 ]) || ([ "$${NODE_VERSION_ARRAY[0]}" -eq 18 ] && [ "$${NODE_VERSION_ARRAY[1]}" -eq 17 ] && [ "$${NODE_VERSION_ARRAY[2]}" -ge 1 ]); then \
			echo "$(BLUE)Node.js $$NODE_VERSION is already installed.$(RESET)"; \
		else \
			echo "$(RED)Node.js 18.17.1 or later is required. Please install Node.js 18.17.1 or later to continue.$(RESET)"; \
			exit 1; \
		fi; \
	else \
		echo "$(RED)Node.js is not installed. Please install Node.js to continue.$(RESET)"; \
		exit 1; \
	fi

check-docker:
	@echo "$(YELLOW)Checking Docker installation...$(RESET)"
	@if command -v docker > /dev/null; then \
		echo "$(BLUE)$(shell docker --version) is already installed.$(RESET)"; \
	else \
		echo "$(RED)Docker is not installed. Please install Docker to continue.$(RESET)"; \
		exit 1; \
	fi

check-poetry:
	@echo "$(YELLOW)Checking Poetry installation...$(RESET)"
	@if command -v poetry > /dev/null; then \
		POETRY_VERSION=$(shell poetry --version 2>&1 | sed -E 's/Poetry \(version ([0-9]+\.[0-9]+\.[0-9]+)\)/\1/'); \
		IFS='.' read -r -a POETRY_VERSION_ARRAY <<< "$$POETRY_VERSION"; \
		if [ $${POETRY_VERSION_ARRAY[0]} -ge 1 ] && [ $${POETRY_VERSION_ARRAY[1]} -ge 8 ]; then \
			echo "$(BLUE)$(shell poetry --version) is already installed.$(RESET)"; \
		else \
			echo "$(RED)Poetry 1.8 or later is required. You can install poetry by running the following command, then adding Poetry to your PATH:"; \
			echo "$(RED) curl -sSL https://install.python-poetry.org | python$(PYTHON_VERSION) -$(RESET)"; \
			echo "$(RED)More detail here: https://python-poetry.org/docs/#installing-with-the-official-installer$(RESET)"; \
			exit 1; \
		fi; \
	else \
		echo "$(RED)Poetry is not installed. You can install poetry by running the following command, then adding Poetry to your PATH:"; \
		echo "$(RED) curl -sSL https://install.python-poetry.org | python$(PYTHON_VERSION) -$(RESET)"; \
		echo "$(RED)More detail here: https://python-poetry.org/docs/#installing-with-the-official-installer$(RESET)"; \
		exit 1; \
	fi

install-python-dependencies:
	@echo "$(GREEN)Installing Python dependencies...$(RESET)"
	@if [ -z "${TZ}" ]; then \
		echo "Defaulting TZ (timezone) to UTC"; \
		export TZ="UTC"; \
	fi
	poetry env use python$(PYTHON_VERSION)
	@if [ "$(shell uname)" = "Darwin" ]; then \
		echo "$(BLUE)Installing chroma-hnswlib...$(RESET)"; \
		export HNSWLIB_NO_NATIVE=1; \
		poetry run pip install chroma-hnswlib; \
	fi
	@poetry install --without llama-index
	@if [ -f "/etc/manjaro-release" ]; then \
		echo "$(BLUE)Detected Manjaro Linux. Installing Playwright dependencies...$(RESET)"; \
		poetry run pip install playwright; \
		poetry run playwright install chromium; \
	else \
		if [ ! -f cache/playwright_chromium_is_installed.txt ]; then \
			echo "Running playwright install --with-deps chromium..."; \
			poetry run playwright install --with-deps chromium; \
			mkdir -p cache; \
			touch cache/playwright_chromium_is_installed.txt; \
		else \
			echo "Setup already done. Skipping playwright installation."; \
		fi \
	fi
	@echo "$(GREEN)Python dependencies installed successfully.$(RESET)"

install-frontend-dependencies:
	@echo "$(YELLOW)Setting up frontend environment...$(RESET)"
	@echo "$(YELLOW)Detect Node.js version...$(RESET)"
	@cd frontend && node ./scripts/detect-node-version.js
	echo "$(BLUE)Installing frontend dependencies with npm...$(RESET)"
	@cd frontend && npm install
	@echo "$(GREEN)Frontend dependencies installed successfully.$(RESET)"

install-pre-commit-hooks:
	@echo "$(YELLOW)Installing pre-commit hooks...$(RESET)"
	@git config --unset-all core.hooksPath || true
	@poetry run pre-commit install --config $(PRE_COMMIT_CONFIG_PATH)
	@echo "$(GREEN)Pre-commit hooks installed successfully.$(RESET)"

lint-backend:
	@echo "$(YELLOW)Running linters...$(RESET)"
	@poetry run pre-commit run --files openhands/**/* agenthub/**/* evaluation/**/* --show-diff-on-failure --config $(PRE_COMMIT_CONFIG_PATH)

lint-frontend:
	@echo "$(YELLOW)Running linters for frontend...$(RESET)"
	@cd frontend && npm run lint

lint:
	@$(MAKE) -s lint-frontend
	@$(MAKE) -s lint-backend

test-frontend:
	@echo "$(YELLOW)Running tests for frontend...$(RESET)"
	@cd frontend && npm run test

test:
	@$(MAKE) -s test-frontend

build-frontend:
	@echo "$(YELLOW)Building frontend...$(RESET)"
	@cd frontend && npm run build

# Start backend
start-backend:
	@echo "$(YELLOW)Starting backend...$(RESET)"
	@poetry run uvicorn openhands.server.listen:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload --reload-exclude "workspace/*"

# Start frontend
start-frontend:
	@echo "$(YELLOW)Starting frontend...$(RESET)"
	@cd frontend && VITE_BACKEND_HOST=$(BACKEND_HOST_PORT) VITE_FRONTEND_PORT=$(FRONTEND_PORT) npm run start

# Common setup for running the app (non-callable)
_run_setup:
	@if [ "$(OS)" = "Windows_NT" ]; then \
		echo "$(RED) Windows is not supported, use WSL instead!$(RESET)"; \
		exit 1; \
	fi
	@mkdir -p logs
	@echo "$(YELLOW)Starting backend server...$(RESET)"
	@poetry run uvicorn openhands.server.listen:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) &
	@echo "$(YELLOW)Waiting for the backend to start...$(RESET)"
	@until nc -z localhost $(BACKEND_PORT); do sleep 0.1; done
	@echo "$(GREEN)Backend started successfully.$(RESET)"

# Run the app (standard mode)
run:
	@echo "$(YELLOW)Running the app...$(RESET)"
	@$(MAKE) -s _run_setup
	@cd frontend && echo "$(BLUE)Starting frontend with npm...$(RESET)" && npm run start -- --port $(FRONTEND_PORT)
	@echo "$(GREEN)Application started successfully.$(RESET)"

# Run the app (in docker)
docker-run: WORKSPACE_BASE ?= $(PWD)/workspace
docker-run:
	@if [ -f /.dockerenv ]; then \
		echo "Running inside a Docker container. Exiting..."; \
		exit 0; \
	else \
		echo "$(YELLOW)Running the app in Docker $(OPTIONS)...$(RESET)"; \
		export WORKSPACE_BASE=${WORKSPACE_BASE}; \
		export SANDBOX_USER_ID=$(shell id -u); \
		export DATE=$(shell date +%Y%m%d%H%M%S); \
		docker compose up $(OPTIONS); \
	fi

# Run the app (WSL mode)
run-wsl:
	@echo "$(YELLOW)Running the app in WSL mode...$(RESET)"
	@$(MAKE) -s _run_setup
	@cd frontend && echo "$(BLUE)Starting frontend with npm (WSL mode)...$(RESET)" && npm run dev_wsl -- --port $(FRONTEND_PORT)
	@echo "$(GREEN)Application started successfully in WSL mode.$(RESET)"

# Setup config.toml
setup-config:
	@echo "$(YELLOW)Setting up config.toml...$(RESET)"
	@$(MAKE) setup-config-prompts
	@mv $(CONFIG_FILE).tmp $(CONFIG_FILE)
	@echo "$(GREEN)Config.toml setup completed.$(RESET)"

setup-config-prompts:
	@echo "[core]" > $(CONFIG_FILE).tmp

	@read -p "Enter your workspace directory (as absolute path) [default: $(DEFAULT_WORKSPACE_DIR)]: " workspace_dir; \
	 workspace_dir=$${workspace_dir:-$(DEFAULT_WORKSPACE_DIR)}; \
	 echo "workspace_base=\"$$workspace_dir\"" >> $(CONFIG_FILE).tmp

	@echo "" >> $(CONFIG_FILE).tmp

	@echo "[llm]" >> $(CONFIG_FILE).tmp
	@read -p "Enter your LLM model name, used for running without UI. Set the model in the UI after you start the app. (see https://docs.litellm.ai/docs/providers for full list) [default: $(DEFAULT_MODEL)]: " llm_model; \
	 llm_model=$${llm_model:-$(DEFAULT_MODEL)}; \
	 echo "model=\"$$llm_model\"" >> $(CONFIG_FILE).tmp

	@read -p "Enter your LLM api key: " llm_api_key; \
	 echo "api_key=\"$$llm_api_key\"" >> $(CONFIG_FILE).tmp

	@read -p "Enter your LLM base URL [mostly used for local LLMs, leave blank if not needed - example: http://localhost:5001/v1/]: " llm_base_url; \
	 if [[ ! -z "$$llm_base_url" ]]; then echo "base_url=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; fi

	@echo "Enter your LLM Embedding Model"; \
		echo "Choices are:"; \
		echo "  - openai"; \
		echo "  - azureopenai"; \
		echo "  - Embeddings available only with OllamaEmbedding:"; \
		echo "    - llama2"; \
		echo "    - mxbai-embed-large"; \
		echo "    - nomic-embed-text"; \
		echo "    - all-minilm"; \
		echo "    - stable-code"; \
		echo "    - bge-m3"; \
		echo "    - bge-large"; \
		echo "    - paraphrase-multilingual"; \
		echo "    - snowflake-arctic-embed"; \
		echo "  - Leave blank to default to 'BAAI/bge-small-en-v1.5' via huggingface"; \
		read -p "> " llm_embedding_model; \
		echo "embedding_model=\"$$llm_embedding_model\"" >> $(CONFIG_FILE).tmp; \
		if [ "$$llm_embedding_model" = "llama2" ] || [ "$$llm_embedding_model" = "mxbai-embed-large" ] || [ "$$llm_embedding_model" = "nomic-embed-text" ] || [ "$$llm_embedding_model" = "all-minilm" ] || [ "$$llm_embedding_model" = "stable-code" ]; then \
			read -p "Enter the local model URL for the embedding model (will set llm.embedding_base_url): " llm_embedding_base_url; \
				echo "embedding_base_url=\"$$llm_embedding_base_url\"" >> $(CONFIG_FILE).tmp; \
		elif [ "$$llm_embedding_model" = "azureopenai" ]; then \
			read -p "Enter the Azure endpoint URL (will overwrite llm.base_url): " llm_base_url; \
				echo "base_url=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure LLM Embedding Deployment Name: " llm_embedding_deployment_name; \
				echo "embedding_deployment_name=\"$$llm_embedding_deployment_name\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure API Version: " llm_api_version; \
				echo "api_version=\"$$llm_api_version\"" >> $(CONFIG_FILE).tmp; \
		fi


# Develop in container
docker-dev:
	@if [ -f /.dockerenv ]; then \
		echo "Running inside a Docker container. Exiting..."; \
		exit 0; \
	else \
		echo "$(YELLOW)Build and run in Docker $(OPTIONS)...$(RESET)"; \
		./containers/dev/dev.sh $(OPTIONS); \
	fi

# Clean up all caches
clean:
	@echo "$(YELLOW)Cleaning up caches...$(RESET)"
	@rm -rf openhands/.cache
	@echo "$(GREEN)Caches cleaned up successfully.$(RESET)"

# Help
help:
	@echo "$(BLUE)Usage: make [target]$(RESET)"
	@echo "Targets:"
	@echo "  $(GREEN)build$(RESET)               - Build project, including environment setup and dependencies."
	@echo "  $(GREEN)lint$(RESET)                - Run linters on the project."
	@echo "  $(GREEN)setup-config$(RESET)        - Setup the configuration for OpenHands by providing LLM API key,"
	@echo "                        LLM Model name, and workspace directory."
	@echo "  $(GREEN)start-backend$(RESET)       - Start the backend server for the OpenHands project."
	@echo "  $(GREEN)start-frontend$(RESET)      - Start the frontend server for the OpenHands project."
	@echo "  $(GREEN)run$(RESET)                 - Run the OpenHands application, starting both backend and frontend servers."
	@echo "                        Backend Log file will be stored in the 'logs' directory."
	@echo "  $(GREEN)docker-dev$(RESET)          - Build and run the OpenHands application in Docker."
	@echo "  $(GREEN)docker-run$(RESET)          - Run the OpenHands application, starting both backend and frontend servers in Docker."
	@echo "  $(GREEN)help$(RESET)                - Display this help message, providing information on available targets."

# Phony targets
.PHONY: build check-dependencies check-python check-npm check-docker check-poetry install-python-dependencies install-frontend-dependencies install-pre-commit-hooks lint start-backend start-frontend run run-wsl setup-config setup-config-prompts help
.PHONY: docker-dev docker-run
