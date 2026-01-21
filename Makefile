.PHONY: up down logs sh test fmt lint

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

sh:
	docker compose run --rm api sh

test:
	docker compose run --rm api pytest -q

fmt:
	docker compose run --rm api sh -c "python -m black . || true"

lint:
	docker compose run --rm api sh -c "python -m ruff check . || true"
