# TokenPulse developer tasks. Backend uses uv; frontend uses npm.

.PHONY: help setup demo backend-test backend-lint frontend-test frontend-lint clean

help:
	@echo "setup          - install backend + frontend deps"
	@echo "demo           - seed synthetic data and start API + dashboard"
	@echo "backend-test   - run backend pytest with coverage"
	@echo "backend-lint   - ruff + mypy"
	@echo "frontend-test  - vitest"
	@echo "frontend-lint  - eslint + tsc"

setup:
	cd backend && uv sync --extra dev
	cd frontend && npm ci

demo:
	bash scripts/demo.sh

backend-test:
	cd backend && uv run pytest --cov --cov-report=term-missing

backend-lint:
	cd backend && uv run ruff check . && uv run mypy

frontend-test:
	cd frontend && npm test

frontend-lint:
	cd frontend && npm run lint && npx tsc -b

clean:
	rm -f backend/*.db backend/*.db-* tokenpulse.db
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache
