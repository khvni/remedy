.PHONY: up down migrate seed lint test scan

up:
	docker compose -f infra/compose.yaml up --build -d

down:
	docker compose -f infra/compose.yaml down -v

migrate:
	alembic -c infra/alembic.ini upgrade head

lint:
	python -m compileall .

test:
	pytest

scan:
	python cli/remedy.py scan $(REPO)
