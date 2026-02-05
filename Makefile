# Makefile pour GOGAinde-Data

.PHONY: help install dev test clean db-init db-migrate scrape-afcon

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Lance les tests
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

db-init:
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
