.PHONY: lint up down migrate_up

COMPOSE = docker-compose -f deploy/local/docker-compose.yaml --env-file ./.env.local
ENV_FILE ?= .env.local

lint:
	uv run ruff check . --fix

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

migrate_up:
	uv run alembic -x env_file="$(ENV_FILE)" upgrade head
