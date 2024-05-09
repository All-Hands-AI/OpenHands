SHELL=/bin/bash
# Makefile for OpenDevin project

# Variables
DOCKER_IMAGE = ghcr.io/opendevin/sandbox
BACKEND_PORT = 3000
BACKEND_HOST = "127.0.0.1:$(BACKEND_PORT)"
FRONTEND_PORT = 3001
DEFAULT_WORKSPACE_DIR = "./workspace"
DEFAULT_MODEL = "gpt-3.5-turbo-1106"
CONFIG_FILE = config.toml
PRECOMMIT_CONFIG_PATH = "./dev_config/python/.pre-commit-config.yaml"

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
ifeq ($(INSTALL_DOCKER),)
	@$(MAKE) -s pull-docker-image
endif
	@$(MAKE) -s install-python-dependencies
	@$(MAKE) -s install-frontend-dependencies
	@$(MAKE) -s install-precommit-hooks
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
	@if command -v python3.11 > /dev/null; then \
		echo "$(BLUE)$(shell python3.11 --version) is already installed.$(RESET)"; \
	else \
		echo "$(RED)Python 3.11 is not installed. Please install Python 3.11 to continue.$(RESET)"; \
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
			echo "$(RED) curl -sSL https://install.python-poetry.org | python3 -$(RESET)"; \
			echo "$(RED)More detail here: https://python-poetry.org/docs/#installing-with-the-official-installer$(RESET)"; \
			exit 1; \
		fi; \
	else \
		echo "$(RED)Poetry is not installed. You can install poetry by running the following command, then adding Poetry to your PATH:"; \
		echo "$(RED) curl -sSL https://install.python-poetry.org | python3.11 -$(RESET)"; \
		echo "$(RED)More detail here: https://python-poetry.org/docs/#installing-with-the-official-installer$(RESET)"; \
		exit 1; \
	fi

pull-docker-image:
	@echo "$(YELLOW)Pulling Docker image...$(RESET)"
	@docker pull $(DOCKER_IMAGE)
	@echo "$(GREEN)Docker image pulled successfully.$(RESET)"

install-python-dependencies:
	@echo "$(GREEN)Installing Python dependencies...$(RESET)"
	@if [ "$(shell uname)" = "Darwin" ]; then \
		echo "$(BLUE)Installing `chroma-hnswlib`...$(RESET)"; \
		export HNSWLIB_NO_NATIVE=1; \
		poetry run pip install chroma-hnswlib; \
	fi
	@poetry install --without evaluation
	@if [ -f "/etc/manjaro-release" ]; then \
		echo "$(BLUE)Detected Manjaro Linux. Installing Playwright dependencies...$(RESET)"; \
		poetry run pip install playwright; \
		poetry run playwright install chromium; \
	else \
		poetry run playwright install --with-deps chromium; \
	fi
	@echo "$(GREEN)Python dependencies installed successfully.$(RESET)"

install-frontend-dependencies:
	@echo "$(YELLOW)Setting up frontend environment...$(RESET)"
	@echo "$(YELLOW)Detect Node.js version...$(RESET)"
	@cd frontend && node ./scripts/detect-node-version.js
	@cd frontend && \
		echo "$(BLUE)Installing frontend dependencies with npm...$(RESET)" && \
		npm install && \
		echo "$(BLUE)Running make-i18n with npm...$(RESET)" && \
		npm run make-i18n
	@echo "$(GREEN)Frontend dependencies installed successfully.$(RESET)"

install-precommit-hooks:
	@echo "$(YELLOW)Installing pre-commit hooks...$(RESET)"
	@git config --unset-all core.hooksPath || true
	@poetry run pre-commit install --config $(PRECOMMIT_CONFIG_PATH)
	@echo "$(GREEN)Pre-commit hooks installed successfully.$(RESET)"

lint-backend:
	@echo "$(YELLOW)Running linters...$(RESET)"
	@poetry run pre-commit run --files $$(git diff --name-only $$(git merge-base main $$(git branch --show-current)) $$(git branch --show-current) | tr '\n' ' ') --show-diff-on-failure --config $(PRECOMMIT_CONFIG_PATH)

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
	@poetry run uvicorn opendevin.server.listen:app --port $(BACKEND_PORT) --reload --reload-exclude "workspace/*"

# Start frontend
start-frontend:
	@echo "$(YELLOW)Starting frontend...$(RESET)"
	@cd frontend && VITE_BACKEND_HOST=$(BACKEND_HOST) VITE_FRONTEND_PORT=$(FRONTEND_PORT) npm run start

# Run the app
run:
	@echo "$(YELLOW)Running the app...$(RESET)"
	@if [ "$(OS)" = "Windows_NT" ]; then \
		echo "$(RED)`make run` is not supported on Windows. Please run `make start-frontend` and `make start-backend` separately.$(RESET)"; \
		exit 1; \
	fi
	@mkdir -p logs
	@echo "$(YELLOW)Starting backend server...$(RESET)"
	@poetry run uvicorn opendevin.server.listen:app --port $(BACKEND_PORT) &
	@echo "$(YELLOW)Waiting for the backend to start...$(RESET)"
	@until nc -z localhost $(BACKEND_PORT); do sleep 0.1; done
	@echo "$(GREEN)Backend started successfully.$(RESET)"
	@cd frontend && echo "$(BLUE)Starting frontend with npm...$(RESET)" && npm run start -- --port $(FRONTEND_PORT)
	@echo "$(GREEN)Application started successfully.$(RESET)"

# Setup config.toml
setup-config:
	@echo "$(YELLOW)Setting up config.toml...$(RESET)"
	@$(MAKE) setup-config-prompts
	@mv $(CONFIG_FILE).tmp $(CONFIG_FILE)
	@echo "$(GREEN)Config.toml setup completed.$(RESET)"

setup-config-prompts:
	@read -p "Enter your LLM Model name, used for running without UI. Set the model in the UI after you start the app. (see https://docs.litellm.ai/docs/providers for full list) [default: $(DEFAULT_MODEL)]: " llm_model; \
	 llm_model=$${llm_model:-$(DEFAULT_MODEL)}; \
	 echo "LLM_MODEL=\"$$llm_model\"" > $(CONFIG_FILE).tmp

	@read -p "Enter your LLM API key: " llm_api_key; \
	 echo "LLM_API_KEY=\"$$llm_api_key\"" >> $(CONFIG_FILE).tmp

	@read -p "Enter your LLM Base URL [mostly used for local LLMs, leave blank if not needed - example: http://localhost:5001/v1/]: " llm_base_url; \
	 if [[ ! -z "$$llm_base_url" ]]; then echo "LLM_BASE_URL=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; fi

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
		echo "  - Leave blank to default to 'BAAI/bge-small-en-v1.5' via huggingface"; \
		read -p "> " llm_embedding_model; \
		echo "LLM_EMBEDDING_MODEL=\"$$llm_embedding_model\"" >> $(CONFIG_FILE).tmp; \
		if [ "$$llm_embedding_model" = "llama2" ] || [ "$$llm_embedding_model" = "mxbai-embed-large" ] || [ "$$llm_embedding_model" = "nomic-embed-text" ] || [ "$$llm_embedding_model" = "all-minilm" ] || [ "$$llm_embedding_model" = "stable-code" ]; then \
			read -p "Enter the local model URL for the embedding model (will set LLM_EMBEDDING_BASE_URL): " llm_embedding_base_url; \
				echo "LLM_EMBEDDING_BASE_URL=\"$$llm_embedding_base_url\"" >> $(CONFIG_FILE).tmp; \
		elif [ "$$llm_embedding_model" = "azureopenai" ]; then \
			read -p "Enter the Azure endpoint URL (will overwrite LLM_BASE_URL): " llm_base_url; \
				echo "LLM_BASE_URL=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure LLM Embedding Deployment Name: " llm_embedding_deployment_name; \
				echo "LLM_EMBEDDING_DEPLOYMENT_NAME=\"$$llm_embedding_deployment_name\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure API Version: " llm_api_version; \
				echo "LLM_API_VERSION=\"$$llm_api_version\"" >> $(CONFIG_FILE).tmp; \
		fi

	@read -p "Enter your workspace directory [default: $(DEFAULT_WORKSPACE_DIR)]: " workspace_dir; \
	 workspace_dir=$${workspace_dir:-$(DEFAULT_WORKSPACE_DIR)}; \
	 echo "WORKSPACE_BASE=\"$$workspace_dir\"" >> $(CONFIG_FILE).tmp

# Clean up all caches
clean:
	@echo "$(YELLOW)Cleaning up caches...$(RESET)"
	@rm -rf opendevin/.cache
	@echo "$(GREEN)Caches cleaned up successfully.$(RESET)"

# Help
help:
	@echo "$(BLUE)Usage: make [target]$(RESET)"
	@echo "Targets:"
	@echo "  $(GREEN)build$(RESET)               - Build project, including environment setup and dependencies."
	@echo "  $(GREEN)lint$(RESET)                - Run linters on the project."
	@echo "  $(GREEN)setup-config$(RESET)        - Setup the configuration for OpenDevin by providing LLM API key,"
	@echo "                        LLM Model name, and workspace directory."
	@echo "  $(GREEN)start-backend$(RESET)       - Start the backend server for the OpenDevin project."
	@echo "  $(GREEN)start-frontend$(RESET)      - Start the frontend server for the OpenDevin project."
	@echo "  $(GREEN)run$(RESET)                 - Run the OpenDevin application, starting both backend and frontend servers."
	@echo "                        Backend Log file will be stored in the 'logs' directory."
	@echo "  $(GREEN)help$(RESET)                - Display this help message, providing information on available targets."

# Phony targets
.PHONY: build check-dependencies check-python check-npm check-docker check-poetry pull-docker-image install-python-dependencies install-frontend-dependencies install-precommit-hooks lint start-backend start-frontend run setup-config setup-config-prompts help
