.PHONY: up down run-queries clean

PYTHON ?= python
COMPOSE ?= docker compose

up:
	$(COMPOSE) up -d --wait mysql

run-queries:
	$(PYTHON) scripts/validate_results.py --mode docker
	$(PYTHON) scripts/build_artifacts.py

down:
	$(COMPOSE) down

clean:
	@echo "Tracked result files are preserved. Use 'make down' to stop the database container."
