# Define make entry and help functionality
.DEFAULT_GOAL := help

.PHONY: help

init: ## Initialize the project and install packages
	@poetry install

format: ## Initialize the project and install packages
	@poetry run black .
	@poetry run isort .

example: ## Execute example application via Poetry
	@poetry run python example.py

tests: ## Execute unit tests
	@TESTING=1 poetry run python -m unittest discover test

update-deps: ## Update the package dependencies via Poetry.
	@poetry update

help: ## Show this help information.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m%-25s\033[0m %s\n", $$1, $$2}'
