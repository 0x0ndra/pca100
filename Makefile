.PHONY: dev check

dev:
	(cd backend && uv run python -m pca.main) & (cd frontend && npm run dev) & wait

check:
	cd backend && uv run ruff check . && uv run mypy pca && uv run pytest && uv run lint-imports && uv run python -m pytest ../desktop/tests
	cd frontend && npm run lint && npm run typecheck && npm test -- --run && npm run depcruise && npm run build
	python3 scripts/check-loc.py
