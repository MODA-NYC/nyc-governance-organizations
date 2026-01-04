SHELL := /bin/bash

.PHONY: setup run test format clean run-pipeline publish-run

# Setup using UV (https://docs.astral.sh/uv/)
# Creates virtual environment and installs all dependencies from lockfile
setup:
	@echo "Setting up project with UV..."
	@uv sync --extra dev --extra appointments
	@echo "Setup complete. Use 'uv run <command>' or 'source .venv/bin/activate'"

# Sync dependencies (useful after pulling changes)
sync:
	@uv sync --extra dev --extra appointments

run:
	@echo "Running main script..."
	@uv run python src/process_golden_dataset.py

test:
	@echo "Running tests..."
	@uv run pytest

run-pipeline:
	@uv run python scripts/pipeline/run_pipeline.py --golden $(GOLDEN) --qa $(QA) --descriptor $(DESCRIPTOR)

publish-run:
	@uv run python scripts/pipeline/publish_run.py --run-dir data/audit/runs/$(RUN_ID) --version $(VERSION) --append-changelog --operator "$(USER)"

format:
	@echo "Formatting code..."
	@echo "Running black..."
	@uv run black .
	@echo "Running ruff (linting and fixing)..."
	@uv run ruff check . --fix
	@echo "Formatting complete."

clean:
	@echo "Cleaning up..."
	@rm -rf .venv
	@rm -rf __pycache__
	@rm -rf */__pycache__
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -f .coverage
	@rm -rf htmlcov
	@echo "Clean complete."
