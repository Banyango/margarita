.PHONY: help install test lint format type-check clean build docs

install:
	uv sync --all-groups

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build-test:
	uv run pyinstaller --onefile --distpath dist src/margarita/cli.py --name margarita

test:  ## Run tests with pytest
	uv run pytest

test-cov:  ## Run tests with coverage
	uv run pytest --cov=margarita --cov-report=html --cov-report=term

lint:  ## Run linting with ruff
	uv run ruff check . --fix

format:  ## Format code with ruff
	uv run ruff format .

format-check:  ## Check code formatting without making changes
	uv run ruff format --check .

type-check:  ## Run type checking with mypy
	uv run mypy src/margarita

check: format-check lint type-check test  ## Run all checks (format, lint, type-check, test)

clean:  ## Clean up build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete

build:  ## Build the package
	uv build

pre-commit-install:  ## Install pre-commit hooks
	uv run pre-commit install

pre-commit-run:  ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

docs:  ## Build documentation
	uv run mkdocs build

docs-serve:  ## Serve documentation locally
	uv run mkdocs serve

