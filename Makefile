.PHONY: backend-test frontend-test ci

backend-test:
	cd backend && poetry install --no-root
	cd backend && poetry run pytest

frontend-test:
	cd frontend && pnpm install --frozen-lockfile
	cd frontend && pnpm test

ci: backend-test frontend-test
