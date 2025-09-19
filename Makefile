.PHONY: build up down logs migrate createsuperuser shell health test test-search

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f | cat

migrate:
	docker compose run --rm api python manage.py migrate --noinput

makemigrations:
	docker compose run --rm api python manage.py makemigrations

createsuperuser:
	docker compose run --rm api python manage.py createsuperuser

shell:
	docker compose run --rm api python manage.py shell

health:
	@echo "Waiting for app..." && sleep 2
	@curl -fsS http://localhost:8001/health/

test:
	docker compose run --rm api python manage.py test

test-search:
	docker compose run --rm api python manage.py test core.test_search -v 2


	