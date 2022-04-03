# Stock prices demo

## Installation
```bash
virtualenv .venv --python=/usr/bin/python3.9
source .venv/bin/activate
pip install --upgrade pip
pip install poetry
poetry install
```

## Local run

Preparations
```bash
docker-compose up
alembic upgrade head
stock-price fill-db
```

Run web-server from terminal window 1
```bash
make run-server
```

Run background job that updates ticker prices from terminal window 2
```
stock-price generate-prices
```

Open [localhost:8000](localhost:8000)
