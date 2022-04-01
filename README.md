# Stock prices demo

## Prepare
```bash
virtualenv .venv --python=/usr/bin/python3.9
source .venv/bin/activate
pip install --upgrade pip
pip install poetry
poetry install
```

## Local run

```bash
docker-compose up -d test_db
alembic upgrade head
make run-server
```
