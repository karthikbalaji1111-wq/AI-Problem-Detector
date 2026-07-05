.PHONY: dev test lint api web docker

dev:
	docker compose up --build

api:
	cd apps/api && uvicorn nexus_api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

test:
	cd apps/api && pytest -q
	cd apps/web && npm run lint

lint:
	cd apps/api && ruff check nexus_api tests
	cd apps/web && npm run lint

docker:
	docker compose build

