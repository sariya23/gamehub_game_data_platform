.PHONY: lint up down

COMPOSE = docker-compose -f deploy/local/docker-compose.yaml --env-file ./.env.local

lint:
	uv run ruff check . --fix

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down
