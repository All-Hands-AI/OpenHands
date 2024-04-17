# Makefile for OpenDevin project

# Variables
DEFAULT_MODEL = "gpt-3.5-turbo-1106"
CONFIG_FILE = config.toml

# ANSI color codes
GREEN=\033[0;32m
YELLOW=\033[0;33m
RED=\033[0;31m
BLUE=\033[0;34m
RESET=\033[0m

# Build
build:
	@echo "$(GREEN)Building project...$(RESET)"
	@$(MAKE) -s check-dependencies
	@$(MAKE) -s docker-build
	@echo "$(GREEN)Build completed successfully.$(RESET)"

check-dependencies:
	@echo "$(YELLOW)Checking dependencies...$(RESET)"
	@$(MAKE) -s check-docker-compose
	@$(MAKE) -s check-poetry
	@echo "$(GREEN)Dependencies checked successfully.$(RESET)"

check-docker-compose:
	@echo "$(YELLOW)Checking Docker Compose installation...$(RESET)"
	@if command -v docker > /dev/null; then \
		echo "$(BLUE)$(shell docker --version) is already installed.$(RESET)"; \
	else \
		echo "$(RED)Docker is not installed.\nPlease install Docker Desktop to continue.$(RESET)"; \
		exit 1; \
	fi

check-poetry:
	@echo "$(YELLOW)Checking Poetry installation...$(RESET)"
	@if command -v poetry > /dev/null; then \
		echo "$(BLUE)$(shell poetry --version) is already installed.$(RESET)"; \
	else \
		echo "$(RED)Poetry is not installed. You can install poetry by running the following command, then adding Poetry to your PATH:"; \
		echo "$(RED) curl -sSL https://install.python-poetry.org | python3 -$(RESET)"; \
		echo "$(RED)More detail here: https://python-poetry.org/docs/#installing-with-the-official-installer$(RESET)"; \
		exit 1; \
	fi

docker-build:
	@read -p "Run 'docker compose down'? [Y/n]: " run_down;
	@if [ ! -z "$$run_down" ] ; then @docker compose down \
  	else exit 0; fi
	@echo "$(YELLOW)Building Docker images...$(RESET)"
	@docker compose -f docker-compose.yml build --pull > /dev/null
	@echo "$(GREEN)Docker images generated successfully.$(RESET)"

docker-rebuild:
	@echo "$(YELLOW)Force rebuilding Docker images...$(RESET)"
	@read -p "Run 'docker compose down'? [Y/n]: " run_down; \
    	 if [ ! -z = "$$run_down" ]; then docker compose down; else exit 0; fi
	@docker compose -f docker-compose.yml build --pull --no-cache
	@echo "$(GREEN)Docker images updated successfully.$(RESET)"

docker-start:
	@echo "$(YELLOW)Starting Docker services...$(RESET)"
	@docker compose up --build
	@echo "$(GREEN)All Docker services started$(RESET)"

# Start backend
start-backend:
	@echo "$(YELLOW)Starting backend...$(RESET)"
	@docker compose up devin

# Start frontend
start-frontend:
	@echo "$(YELLOW)Starting frontend...$(RESET)"
	@docker compose up web_ui

# Run the app
run:
	@echo "$(YELLOW)Running the app...$(RESET)"
	@if [ "$(OS)" = "Windows_NT" ]; then \
		echo "$(RED)`make run` is not supported on Windows. Please run `make start-frontend` and `make start-backend` separately.$(RESET)"; \
		exit 1; \
	fi
	@mkdir -p logs
	@echo "$(YELLOW)Starting backend server...$(RESET)"
	@$(MAKE) docker-start
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
	@read -p "Enter your LLM Model name (see https://docs.litellm.ai/docs/providers for full list) [default: $(DEFAULT_MODEL)]: " llm_model; \
	 llm_model=$${llm_model:-$(DEFAULT_MODEL)}; \
	 echo "LLM_MODEL=\"$$llm_model\"" > $(CONFIG_FILE).tmp

	@read -p "Enter your LLM API key: " llm_api_key; \
	 echo "LLM_API_KEY=\"$$llm_api_key\"" >> $(CONFIG_FILE).tmp

	@read -p "Enter your LLM Base URL [mostly used for local LLMs, leave blank if not needed - example: http://localhost:5001/v1/]: " llm_base_url; \
	 if [[ ! -z "$$llm_base_url" ]]; then echo "LLM_BASE_URL=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; fi

	@echo "Enter your LLM Embedding Model\nChoices are openai, azureopenai, llama2 or leave blank to default to 'BAAI/bge-small-en-v1.5' via huggingface"; \
	 read -p "> " llm_embedding_model; \
	 	echo "LLM_EMBEDDING_MODEL=\"$$llm_embedding_model\"" >> $(CONFIG_FILE).tmp; \
		if [ "$$llm_embedding_model" = "llama2" ]; then \
			read -p "Enter the local model URL (will overwrite LLM_BASE_URL): " llm_base_url; \
				echo "LLM_BASE_URL=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; \
		elif [ "$$llm_embedding_model" = "azureopenai" ]; then \
			read -p "Enter the Azure endpoint URL (will overwrite LLM_BASE_URL): " llm_base_url; \
				echo "LLM_BASE_URL=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure LLM Deployment Name: " llm_deployment_name; \
				echo "LLM_DEPLOYMENT_NAME=\"$$llm_deployment_name\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure API Version: " llm_api_version; \
				echo "LLM_API_VERSION=\"$$llm_api_version\"" >> $(CONFIG_FILE).tmp; \
		fi

	@read -p "Enter your workspace directory [default: $(DEFAULT_WORKSPACE_DIR)]: " workspace_dir; \
	 workspace_dir=$${workspace_dir:-$(DEFAULT_WORKSPACE_DIR)}; \
	 echo "WORKSPACE_DIR=\"$$workspace_dir\"" >> $(CONFIG_FILE).tmp

# Help
help:
	@echo "$(BLUE)Usage: make [target]$(RESET)"
	@echo "Targets:"
	@echo "  $(GREEN)build$(RESET)               - Build project, including environment setup and dependencies."
	@echo "  $(GREEN)setup-config$(RESET)        - Setup the configuration for OpenDevin by providing LLM API key,"
	@echo "                        LLM Model name, and workspace directory."
	@echo "  $(GREEN)start-backend$(RESET)       - Start the backend server for the OpenDevin project."
	@echo "  $(GREEN)start-frontend$(RESET)      - Start the frontend server for the OpenDevin project."
	@echo "  $(GREEN)run$(RESET)                 - Run the OpenDevin application, starting both backend and frontend servers."
	@echo "                        Backend Log file will be stored in the 'logs' directory."
	@echo "  $(GREEN)help$(RESET)                - Display this help message, providing information on available targets."

# Phony targets
.PHONY: build check-dependencies check-docker check-poetry setup-config setup-config-prompts docker-build docker-start help
