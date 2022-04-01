import pathlib
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus
from uuid import uuid4

import pytest
import sqlalchemy as sa
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from starlette.templating import Jinja2Templates

from stock_prices import db
from stock_prices.app import get_app
from stock_prices.cli import _update_prices
from stock_prices.views import get_template


@pytest.fixture()
def client():
    static_path = pathlib.Path(__file__).parent.parent / 'static'
    app = get_app(static_directory=static_path)
    app.dependency_overrides[get_template] = lambda: Jinja2Templates(static_path / 'templates')
    return TestClient(app)


@pytest.fixture(autouse=True)
def _prepare_db():
    settings = db.DBSettings()
    settings.setup(echo=True)
    engine = sa.create_engine(url=settings.url)
    db.Base.metadata.bind = engine
    db.Base.metadata.drop_all()
    db.Base.metadata.create_all()
    yield
    db.Base.metadata.drop_all()


def _create_ticker_price(prices):
    ticker_name = str(uuid4())
    with db.create_session() as session:
        ticker = db.Ticker(name=ticker_name)
        ticker_prices = [
            db.TickerPrice(ticker=ticker, price=price, created_at=created_at) for created_at, price in prices.items()
        ]
        session.add_all((ticker, *ticker_prices))
    return ticker_name


def test_homepage(client):
    ticker_name = _create_ticker_price(prices={})

    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert ticker_name in response.text


@pytest.mark.parametrize('limit', [5, 10, 20])
def test_get_ticker_price(client, limit):
    prices_number = 15
    ticker_name = _create_ticker_price(
        prices={datetime(year=2022, month=3, day=d): d for d in range(1, prices_number + 1)}
    )
    _create_ticker_price(prices={datetime(year=2022, month=3, day=d): d for d in range(1, 10)})

    response = client.get('/ticker-price', params={'ticker_name': ticker_name, 'limit': limit})

    assert response.status_code == HTTPStatus.OK
    expected = list(range(1, prices_number + 1))[-limit:]
    assert [(p['name'], p['price']) for p in response.json()] == [(ticker_name, p) for p in expected]


@pytest.mark.parametrize(
    ('older_than', 'expected_prices'),
    [
        (datetime(year=2022, month=1, day=9, hour=12), [1, 2, 3]),
        (datetime(year=2022, month=3, day=1, hour=12), [2, 3]),
        (datetime(year=2022, month=3, day=2, hour=12), [3]),
        (datetime(year=2022, month=3, day=3, hour=12), []),
    ],
)
def test_track_price_web_socket(client, older_than, expected_prices):
    ticker_name = _create_ticker_price(prices={datetime(year=2022, month=3, day=d): d for d in [1, 2, 3]})
    _create_ticker_price(prices={datetime(year=2022, month=3, day=d): d for d in range(1, 10)})

    with client.websocket_connect('/track-price') as websocket:
        websocket.send_json([ticker_name, jsonable_encoder(older_than)])
        data = websocket.receive_json()

    assert [(p['name'], p['price']) for p in data] == [(ticker_name, p) for p in expected_prices]


def test_update_prices():
    t1_price, t2_price = 15, 29
    ticker_name1 = _create_ticker_price(prices={datetime(year=2022, month=3, day=1): t1_price})
    ticker_name2 = _create_ticker_price(prices={datetime(year=2022, month=3, day=1): t2_price})

    _update_prices(price_diff_generator=lambda: 1)

    with db.create_session() as session:
        for name, initial_price in zip([ticker_name1, ticker_name2], [t1_price, t2_price]):
            ticker: db.Ticker = session.query(db.Ticker).filter(db.Ticker.name == name).one()
            assert len(ticker.prices) == 2
            assert [p.price for p in ticker.prices] == [Decimal(initial_price), Decimal(initial_price + 1)]
