.PHONY: help install dev test clean live-tracker docker-init docker-up docker-down docker-logs

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installer dépendances
	pip install -r requirements.txt

db-init: ## Initialiser DB
	python -m app.db.models

dev: ## Lancer API en local
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Tests complets
	pytest tests/ -v

test-cov: ## Tests avec couverture
	pytest --cov=app --cov-report=html

test-api: ## Tests API seulement
	pytest tests/test_api.py -v

test-live: ## Tests live seulement
	pytest tests/test_live.py -v

clean: ## Nettoyer cache Python
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

scrape-data: ## Ingestion AFCON locale
	python pipeline/ingest_afcon.py || true
	python pipeline/ingest_friendlies.py

live-tracker: ## Lancer tracker live local
	python -m app.live_tracker

live-status: ## Voir matchs en cache Redis
	redis-cli KEYS "live:*"

live-clear: ## Vider cache Redis
	redis-cli FLUSHDB


PROJECT_ROOT := $(shell pwd)

AIRFLOW_HOME := $(PROJECT_ROOT)/airflow
VENV_DIR     := $(PROJECT_ROOT)/.venv-airflow
AIRFLOW_BIN  := $(VENV_DIR)/bin/airflow
VENV_PATH    := $(VENV_DIR)/bin

airflow-init:
	@echo "🔧 Initializing Airflow..."
	PATH=$(VENV_PATH):$$PATH \
	AIRFLOW_HOME=$(AIRFLOW_HOME) \
	$(AIRFLOW_BIN) db migrate && \
	PATH=$(VENV_PATH):$$PATH \
	AIRFLOW_HOME=$(AIRFLOW_HOME) \
	$(AIRFLOW_BIN) users create \
		--username admin \
		--password admin \
		--firstname Admin \
		--lastname Admin \
		--role Admin \
		--email admin@example.com

airflow-webserver:
	PATH=$(VENV_PATH):$$PATH \
	AIRFLOW_HOME=$(AIRFLOW_HOME) \
	$(AIRFLOW_BIN) webserver --port 8080

airflow-scheduler:
	PATH=$(VENV_PATH):$$PATH \
	AIRFLOW_HOME=$(AIRFLOW_HOME) \
	$(AIRFLOW_BIN) scheduler

airflow-start:
	make -j2 airflow-webserver airflow-scheduler

airflow-reset:
	rm -rf $(AIRFLOW_HOME)/airflow.db
	rm -rf $(AIRFLOW_HOME)/logs


docker-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-build:
	docker compose -f docker/docker-compose.yml build

docker-down:
	docker compose -f docker/docker-compose.yml down

docker-init:
	docker compose -f docker/docker-compose.yml up airflow-init