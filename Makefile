# Makefile for OpenDevin project

# Variables
DOCKER_IMAGE = ghcr.io/opendevin/sandbox
BACKEND_PORT = 3000
BACKEND_HOST = "127.0.0.1:$(BACKEND_PORT)"
FRONTEND_PORT = 3001
DEFAULT_WORKSPACE_DIR = "./workspace"
DEFAULT_MODEL = "gpt-4-0125-preview"
CONFIG_FILE = config.toml

# Build
build:
	@echo "Building project..."
	@echo "Pulling Docker image..."
	@docker pull $(DOCKER_IMAGE)
	@echo "Installing Python dependencies..."
	@python -m pip install pipenv
	@python -m pipenv install -v
	@echo "Setting up frontend environment..."
	@echo "Detect Node.js version..."
	@cd frontend && node ./scripts/detect-node-version.js
	@cd frontend && if [ -f node_modules/.package-lock.json ]; then \
		echo "This project currently uses "pnpm" for dependency management. It has detected that dependencies were previously installed using "npm" and has automatically deleted the "node_modules" directory to prevent unnecessary conflicts."; \
		rm -rf node_modules; \
	fi
	@which corepack > /dev/null || (echo "Installing corepack..." && npm install -g corepack)
	@cd frontend && corepack enable && pnpm install && pnpm run make-i18n

# Start backend
start-backend:
	@echo "Starting backend..."
	@python -m pipenv run uvicorn opendevin.server.listen:app --port $(BACKEND_PORT)

# Start frontend
start-frontend:
	@echo "Starting frontend..."
	@cd frontend && BACKEND_HOST=$(BACKEND_HOST) FRONTEND_PORT=$(FRONTEND_PORT) npm run start

# Run the app
run:
	@echo "Running the app..."
	@if [ "$(OS)" == "Windows_NT" ]; then \
		echo "`make run` is not supported on Windows. Please run `make start-frontend` and `make start-backend` separately."; \
		exit 1; \
	fi
	@mkdir -p logs
	@rm -f logs/pipe
	@mkfifo logs/pipe
	@cat logs/pipe | (make start-backend) &
	@echo 'test' | tee logs/pipe | (make start-frontend)

# Setup config.toml
setup-config:
	@echo "Setting up config.toml..."
	@read -p "Enter your LLM Model name (see docs.litellm.ai/docs/providers for full list) [default: $(DEFAULT_MODEL)]: " llm_model; \
	 llm_model=$${llm_model:-$(DEFAULT_MODEL)}; \
	 echo "LLM_MODEL=\"$$llm_model\"" >> $(CONFIG_FILE).tmp

	@read -p "Enter your LLM API key: " llm_api_key; \
	 echo "LLM_API_KEY=\"$$llm_api_key\"" >> $(CONFIG_FILE).tmp

	@echo "Enter your LLM Embedding Model\nChoices are openai, azureopenai, llama2 or leave blank to default to 'BAAI/bge-small-en-v1.5' via huggingface"; \
	 read -p "> " llm_embedding_model; \
	 	echo "LLM_EMBEDDING_MODEL=\"$$llm_embedding_model\"" >> $(CONFIG_FILE).tmp; \
		if [ "$$llm_embedding_model" = "llama2" ]; then \
			read -p "Enter the local model URL: " llm_base_url; \
				echo "LLM_BASE_URL=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; \
		elif [ "$$llm_embedding_model" = "azureopenai" ]; then \
			read -p "Enter the Azure endpoint URL: " llm_base_url; \
				echo "LLM_BASE_URL=\"$$llm_base_url\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure LLM Deployment Name: " llm_deployment_name; \
				echo "LLM_DEPLOYMENT_NAME=\"$$llm_deployment_name\"" >> $(CONFIG_FILE).tmp; \
			read -p "Enter the Azure API Version: " llm_api_version; \
				echo "LLM_API_VERSION=\"$$llm_api_version\"" >> $(CONFIG_FILE).tmp; \
		fi

	@read -p "Enter your workspace directory [default: $(DEFAULT_WORKSPACE_DIR)]: " workspace_dir; \
	 workspace_dir=$${workspace_dir:-$(DEFAULT_WORKSPACE_DIR)}; \
	 echo "WORKSPACE_DIR=\"$$workspace_dir\"" >> $(CONFIG_FILE).tmp

	@mv $(CONFIG_FILE).tmp $(CONFIG_FILE)

# Help
help:
	@echo "Usage: make [target]"
	@echo "Targets:"
	@echo "  build               - Build project, including environment setup and dependencies."
	@echo "  start-backend       - Start the backend server for the OpenDevin project."
	@echo "  start-frontend      - Start the frontend server for the OpenDevin project."
	@echo "  run                 - Run the OpenDevin application, starting both backend and frontend servers."
	@echo "                        Backend Log file will be stored in the 'logs' directory."
	@echo "  setup-config        - Setup the configuration for OpenDevin by providing LLM API key, LLM Model name, and workspace directory."
	@echo "  help                - Display this help message, providing information on available targets."

# Phony targets
.PHONY: install start-backend start-frontend run setup-config help
