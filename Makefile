.PHONY: build up down logs migrate createsuperuser shell health test test-unit test-integration test-utils test-phase8

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

# Test Commands
test:
	docker compose run --rm api python manage.py test

test-unit:
	docker compose run --rm api python manage.py test tests.unit --parallel

test-integration:
	docker compose run --rm api python manage.py test tests.integration --parallel

test-fast:
	docker compose run --rm api python manage.py test tests.unit tests.integration --parallel

test-utils:
	docker compose run --rm api python manage.py test tests.unit.test_utils -v 2

test-serializers:
	docker compose run --rm api python manage.py test tests.unit.test_serializers -v 2

test-distance:
	docker compose run --rm api python manage.py test tests.unit.test_distance_calculations -v 2

test-api-validation:
	docker compose run --rm api python manage.py test tests.integration.test_api_validation -v 2

test-search-logic:
	docker compose run --rm api python manage.py test tests.integration.test_search_logic -v 2

test-advanced:
	docker compose run --rm api python manage.py test tests.integration.test_advanced_features -v 2

test-production:
	docker compose run --rm api python manage.py test tests.integration.test_production_ready -v 2

test-phase8:
	docker compose run --rm api python manage.py test tests.test_search.BusinessSearchPhase8Test -v 2

# Database Commands
optimize-db:
	docker compose run --rm api python manage.py optimize_database

optimize-db-dry-run:
	docker compose run --rm api python manage.py optimize_database --dry-run


	