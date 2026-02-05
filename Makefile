# .PHONY: up down logs sh test fmt lint

# up:
# 	docker compose up --build

# down:
# 	docker compose down -v

# logs:
# 	docker compose logs -f --tail=200

# sh:
# 	docker compose run --rm api sh

# test:
# 	docker compose run --rm api pytest -q

# fmt:
# 	docker compose run --rm api sh -c "python -m black . || true"

# lint:
# 	docker compose run --rm api sh -c "python -m ruff check . || true"


# Makefile pour GOGAinde-Data

.PHONY: help install dev test clean db-init db-migrate scrape-afcon

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances
	pip install -r requirements.txt

dev: ## Lance l'application en mode développement
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Lance les tests
	pytest tests/ -v

clean: ## Nettoie les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

db-init: ## Initialise la base de données
	python -m app.db.models

db-migrate: ## Lance les migrations Alembic
	alembic upgrade head

scrape-afcon: ## Lance le scraping AFCON
	python pipeline/ingest_afcon.py

docker-up: ## Lance les conteneurs Docker
	docker-compose up -d

docker-down: ## Arrête les conteneurs Docker
	docker-compose down

docker-logs: ## Affiche les logs Docker
	docker-compose logs -f

notebook: ## Lance Jupyter
	jupyter notebook notebooks/
