SHELL := /bin/bash

# Variables
PYTHON_EXEC := $(shell pyenv which python3)
PYTHON = .venv/bin/python
PIP = .venv/bin/pip

.PHONY: setup run test format clean

setup:
	echo "Starting setup process..."
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment .venv using $(PYTHON_EXEC)..."; \
		$(PYTHON_EXEC) -m venv .venv; \
		echo "Upgrading pip, setuptools, and wheel in .venv using $(PYTHON_EXEC)..."; \
		$(PYTHON_EXEC) -m pip install --upgrade pip setuptools wheel; \
		echo "Activating venv and installing project dependencies in editable mode using .venv/bin/pip..."; \
		source .venv/bin/activate; \
		$(PIP) install -e ".[dev]"; \
		echo "Setup complete. Virtual environment '.venv' is ready."; \
	else \
		echo "Virtual environment '.venv' already exists."; \
		echo "Ensuring pip, setuptools, and wheel are up to date in .venv using $(PYTHON_EXEC)..."; \
		$(PYTHON_EXEC) -m pip install --upgrade pip setuptools wheel; \
		echo "Activating venv and installing/updating project dependencies in editable mode using .venv/bin/pip..."; \
		source .venv/bin/activate; \
		$(PIP) install -e ".[dev]"; \
		echo "Dependencies updated in existing virtual environment '.venv'."; \
	fi

run:
	echo "Running main script..."
	@$(PYTHON) src/process_golden_dataset.py

test:
	echo "Running tests..."
	@$(PYTHON) -m pytest

.PHONY: run-prepare run-publish-dry run-publish-apply
run-prepare:
	@$(PYTHON) scripts/maint/prepare_run_proposed_changes.py --run-id $(RUN_ID) --step1 data/output/changelog_step1.csv --step2 data/output/changelog_step2.csv
run-publish-dry:
	@$(PYTHON) scripts/maint/publish_changelog_run.py --run-dir data/audit/runs/$(RUN_ID)
run-publish-apply:
	@$(PYTHON) scripts/maint/publish_changelog_run.py --run-dir data/audit/runs/$(RUN_ID) --apply --commit --operator "$(USER)"

format:
	echo "Formatting code..."
	echo "Running black..."
	@$(PYTHON) -m black .
	echo "Running ruff (linting and fixing)..."
	@$(PYTHON) -m ruff check . --fix
	echo "Formatting complete."

# Consider adding a clean target as well
clean:
	echo "Cleaning up..."
	@rm -rf .venv
	@rm -rf __pycache__
	@rm -rf */__pycache__
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -f .coverage
	@rm -rf htmlcov
	echo "Clean complete."
