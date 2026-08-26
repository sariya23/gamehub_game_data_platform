.PHONY: lint up down migrate_up

ENV_FILE ?= .env.local
COMPOSE = docker-compose -f deploy/local/docker-compose.yaml --env-file "$(ENV_FILE)"

lint:
	uv run ruff check . --fix

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

migrate_up:
	uv run alembic -x env_file="$(ENV_FILE)" upgrade head
