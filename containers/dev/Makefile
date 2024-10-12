#
# make
#
.DEFAULT_GOAL := help

.PHONY: help
help: Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

##
build: image ## Same as image
image: ## Build dev image
	@echo "Building..."
	@docker buildx bake

dev: ## Build and run OpenHands in container
	@echo "Running..."
	@./dev.sh

.PHONY: build image dev
##
