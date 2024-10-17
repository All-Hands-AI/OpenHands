#
# make
#
.DEFAULT_GOAL := help

.PHONY: help
help: Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

##
build: image ## Same as image

image: ## Build custom sandbox image
	@echo "Building docker images..."
	@docker buildx bake

run: run-dind ## Same as run-dind

run-dind: ## Run docker in docker in container
	@echo "Running..."
	@docker compose --profile dind run --rm sandbox-dind

run-host: ## Run docker in docker via host docker.sock
	@echo "Running on host ..."
	@docker compose --profile host run --rm sandbox-host

.PHONY: build run run-dind run-host image
##
