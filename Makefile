# Makefile for OpenDevin project

# Variables
DOCKER_IMAGE = ghcr.io/opendevin/sandbox
BACKEND_PORT = 3000
FRONTEND_PORT = 3001
DEFAULT_WORKSPACE_DIR = "./workspace"
CONFIG_FILE = config.toml

# Build
build:
	@echo "Building project..."
	@echo "Pulling Docker image..."
	@docker pull $(DOCKER_IMAGE)
	@echo "Installing Python dependencies..."
	@pip install pipenv
	@pipenv install -v
	@echo "Setting up frontend environment..."
	@cd frontend && npm install

# Start backend
start-backend:
	@echo "Starting backend..."
	@pipenv run uvicorn opendevin.server.listen:app --port $(BACKEND_PORT)

# Start frontend
start-frontend:
	@echo "Starting frontend..."
	@cd frontend && npm run start -- --port $(FRONTEND_PORT)

# Run the app
run:
	@echo "Running the app..."
	@rm logs/pipe
	@mkfifo logs/pipe
	@cat logs/pipe | (make start-backend) &
	@echo 'test' | tee logs/pipe | (make start-frontend)

# Setup config.toml
setup-config:
	@echo "Setting up config.toml..."
	@read -p "Enter your LLM API key: " llm_api_key; \
	 echo "LLM_API_KEY=\"$$llm_api_key\"" >> $(CONFIG_FILE).tmp
	@read -p "Enter your LLM Model name [default: gpt-4-0125-preview]: " llm_model; \
	 echo "LLM_MODEL=\"$$llm_model\"" >> $(CONFIG_FILE).tmp
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
