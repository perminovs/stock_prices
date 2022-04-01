.PHONY: test lint pretty plint run-server

BIN = .venv/bin/
CODE = stock_prices
DB_VERSIONS = alembic/versions
TEST = tests

test:
	PYTHONPATH=$(CODE) $(BIN)pytest --verbosity=2 --showlocals --strict $(TEST)

lint:
	$(BIN)flake8 --jobs 4 --statistics --show-source $(CODE) $(TEST)
	$(BIN)mypy $(CODE)
	$(BIN)black --target-version py36 --skip-string-normalization --line-length=119 --check $(CODE) $(TEST)

pretty:
	$(BIN)isort $(CODE) $(TEST)
	$(BIN)black --target-version py36 --skip-string-normalization --line-length=119 $(CODE) $(TEST) $(DB_VERSIONS)
	$(BIN)unify --in-place --recursive $(CODE) $(TEST)

plint: pretty lint

run-server:
	uvicorn stock_prices.asgi:app --reload
