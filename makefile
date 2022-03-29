.PHONY: test lint pretty plint

BIN = .venv/bin/
CODE = stock_prices
TEST = tests

test:
	PYTHONPATH=$(CODE) $(BIN)pytest --verbosity=2 --showlocals --strict $(TEST)

lint:
	$(BIN)flake8 --jobs 4 --statistics --show-source $(CODE) $(TEST)
	$(BIN)mypy $(CODE) $(TEST)
	$(BIN)black --target-version py36 --skip-string-normalization --line-length=119 --check $(CODE) $(TEST)

pretty:
	$(BIN)isort $(CODE) $(TEST)
	$(BIN)black --target-version py36 --skip-string-normalization --line-length=119 $(CODE) $(TEST)
	$(BIN)unify --in-place --recursive $(CODE) $(TEST)

plint: pretty lint
