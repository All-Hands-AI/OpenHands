#
# make openhands cli
#
.DEFAULT_GOAL := help

.PHONY: help

help: Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

#
build: docker-build ## Same as docker-build
run: run-cli ## Same as run-cli
clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	@rm -rf dist/*

docker-build: ## Build openhands cli with docker for linux/macos/windows
	@echo "Building openhands cli with docker..."
	@./build.sh

build-cli: ## Build openhands cli on host for linux/macos/windows (go toolchain required)
	@echo "Building openhands cli with go toolchain on host..."
	@./build-cli.sh

run-cli: ## Run openhands cli on host with ARGS="..."
	@echo "Running openhands cli on host $(ARGS)..."
	@./run-cli.sh $(ARGS)

tidy: ## Tidy up openhands cli source on host (go toolchain required)
	@echo "Tidying go modules..."
	@go fmt ./...; \
		go vet ./...; \
		go mod tidy;

.PHONY: build run clean docker-build build-cli run-cli tidy

##
