APP_DIR := app
UV := uv
PY := $(UV) run python
ALEMBIC := $(UV) run alembic -c $(APP_DIR)/alembic.ini

.PHONY: help sync run migrate upgrade revision test test_docker

help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  sync         Sync project virtualenv (runs 'uv sync' in the app folder)"
	@echo "  run          Sync then run the application (runs 'python main.py' inside uv venv)"
	@echo "  migrate      Alias for 'upgrade' (applies migrations)"
	@echo "  upgrade      Run alembic upgrade head"
	@echo "  revision     Create an alembic revision with message: make revision M=\"message\""
	@echo "  test  		  Run tests in Docker container"

sync:
	@echo "Syncing virtualenv in $(APP_DIR)..."
	cd $(APP_DIR) && $(UV) sync

run: sync
	@echo "Starting app..."
	cd $(APP_DIR) && $(PY) main.py

migrate: upgrade

upgrade:
	@echo "Applying migrations (alembic upgrade head)..."
	cd $(APP_DIR) && $(ALEMBIC) upgrade head

revision:
	@if [ -z "$(M)" ]; then \
		echo "Please provide a message: make revision M=\"message\""; exit 1; \
	fi
	@echo "Creating revision: $(M)"
	cd $(APP_DIR) && $(ALEMBIC) revision --autogenerate -m "$(M)"

test:
	@echo "Running tests in Docker..."
	@docker compose run --remove-orphans backend bash -c "uv run pytest -n auto ./tests"
	