.PHONY: help install dev test clean live-tracker docker-init docker-up docker-down docker-logs

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installer dépendances
	pip install -r requirements.txt

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

scrape-afcon: ## Ingestion AFCON locale
	python pipeline/ingest_afcon.py

live-tracker: ## Lancer tracker live local
	python -m app.live_tracker

live-status: ## Voir matchs en cache Redis
	redis-cli KEYS "live:*"

live-clear: ## Vider cache Redis
	redis-cli FLUSHDB

# docker-init: ## Initialiser Docker (première fois)
# 	mkdir -p airflow/dags airflow/logs airflow/plugins airflow/config
# 	cp .env.example .env
# 	@echo "Éditer .env avec tes valeurs avant docker-up"

# docker-up: ## Démarrer tous les conteneurs
# 	docker-compose up -d

# docker-down: ## Arrêter conteneurs
# 	docker-compose down

# docker-restart: ## Redémarrer conteneurs
# 	docker-compose restart

# docker-logs: ## Logs temps réel
# 	docker-compose logs -f

# docker-logs-api: ## Logs API seulement
# 	docker-compose logs -f api

# docker-logs-live: ## Logs live tracker
# 	docker-compose logs -f live_tracker

# docker-logs-airflow: ## Logs Airflow
# 	docker-compose logs -f airflow-scheduler

# docker-ps: ## Statut conteneurs
# 	docker-compose ps

# docker-rebuild: ## Rebuild après modif code
# 	docker-compose build --no-cache
# 	docker-compose up -d

# docker-clean: ## Supprimer tout (+ volumes)
# 	docker-compose down -v

# docker-test: ## Tests dans Docker
# 	docker-compose exec api pytest tests/ -v

# docker-shell-api: ## Shell dans conteneur API
# 	docker-compose exec api bash

# docker-shell-airflow: ## Shell dans Airflow
# 	docker-compose exec airflow-webserver bash

# db-migrate: ## Migration DB dans Docker
# 	docker-compose exec api alembic upgrade head

# airflow-dags: ## Lister DAGs Airflow
# 	docker-compose exec airflow-webserver airflow dags list

# airflow-trigger-afcon: ## Déclencher DAG AFCON manuellement
# 	docker-compose exec airflow-scheduler airflow dags trigger ingest_afcon

# airflow-trigger-multi: ## Déclencher DAG multi-compétitions
# 	docker-compose exec airflow-scheduler airflow dags trigger ingest_multi_competitions

# airflow-trigger-fixtures: ## Trigger DAG fixtures
# 	docker-compose exec airflow-scheduler airflow dags trigger ingest_fixtures

# airflow-trigger-lineups: ## Trigger DAG lineups
# 	docker-compose exec airflow-scheduler airflow dags trigger ingest_lineups

# airflow-trigger-details: ## Trigger DAG match details
# 	docker-compose exec airflow-scheduler airflow dags trigger ingest_match_details

# airflow-trigger-standings: ## Trigger DAG standings
# 	docker-compose exec airflow-scheduler airflow dags trigger ingest_standings_cupstree

# airflow-trigger-stats: ## Trigger DAG season stats
# 	docker-compose exec airflow-scheduler airflow dags trigger ingest_season_statistics