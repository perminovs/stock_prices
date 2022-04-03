import asyncio
import json
import pathlib
from datetime import datetime, timezone
from decimal import Decimal
from http import HTTPStatus
from uuid import uuid4

import pytest
import sqlalchemy as sa
from aioredis import RedisError
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from starlette.templating import Jinja2Templates
from starlette.websockets import WebSocketDisconnect

import stock_prices.settings
from stock_prices import db
from stock_prices.app import get_app
from stock_prices.cli import _update_prices
from stock_prices.models import RedisPriceMessage
from stock_prices.views import WebSocketCloseCode, get_redis, get_template


@pytest.fixture()
def redis_client():
    return asyncio.run(get_redis())


@pytest.fixture()
def client():
    static_path = pathlib.Path(__file__).parent.parent / 'static'
    app = get_app(static_directory=static_path)
    app.dependency_overrides[get_template] = lambda: Jinja2Templates(static_path / 'templates')
    return TestClient(app)


@pytest.fixture()
def price_update(request):
    return request.param


@pytest.fixture()
def _mock_redis_channel(price_update, mocker):
    message = {'type': 'message', 'data': json.dumps(jsonable_encoder(price_update))}

    _get_message = mocker.patch('stock_prices.views._get_message')
    _get_message.side_effect = [message, RedisError()]


@pytest.fixture(autouse=True)
def _prepare_db():
    settings = stock_prices.settings.DBSettings()
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


def test_get_ticker_price(client):
    ticker_name = _create_ticker_price(prices={datetime(year=2022, month=3, day=d): d for d in range(1, 16)})
    _create_ticker_price(prices={datetime(year=2022, month=3, day=d): d for d in range(1, 10)})

    response = client.get('/ticker-price', params={'ticker_name': ticker_name})

    assert response.status_code == HTTPStatus.OK
    assert [(p['name'], p['price']) for p in response.json()] == [(ticker_name, p) for p in range(1, 16)]


@pytest.mark.parametrize(
    'price_update',
    [{'price': 15, 'created_at': datetime(year=2022, month=3, day=1), 'name': 'some-ticker'}],
    indirect=True,
)
@pytest.mark.usefixtures('_mock_redis_channel')
def test_track_price_websocket(client, redis_client, price_update):
    with client.websocket_connect('/track-price') as websocket:
        websocket.send_text('some-ticker')
        data = websocket.receive_json()
        assert data['price'] == price_update['price']

        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_json()
        assert error.value.code == WebSocketCloseCode.TRY_AGAIN_LATER


@pytest.mark.parametrize(
    'price_update',
    [{'price': 15, 'created_at': datetime(year=2022, month=3, day=1)}],
    indirect=True,
)
@pytest.mark.usefixtures('_mock_redis_channel')
def test_track_price_invalid_message(client, redis_client, price_update):
    with client.websocket_connect('/track-price') as websocket:
        websocket.send_text('some-ticker')
        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_json()
        assert error.value.code == WebSocketCloseCode.INTERNAL_ERROR


def test_update_prices():
    t1_price, t2_price = 15, 29
    ticker_name1 = _create_ticker_price(prices={datetime(year=2022, month=3, day=1): t1_price})
    ticker_name2 = _create_ticker_price(prices={datetime(year=2022, month=3, day=1): t2_price})

    _update_prices(price_diff_generator=lambda: 1, publish=False)

    with db.create_session() as session:
        for name, initial_price in zip([ticker_name1, ticker_name2], [t1_price, t2_price]):
            ticker: db.Ticker = session.query(db.Ticker).filter(db.Ticker.name == name).one()
            assert len(ticker.prices) == 2
            assert [p.price for p in ticker.prices] == [Decimal(initial_price), Decimal(initial_price + 1)]


def test_parse_redis_message():
    msg = {
        'type': 'message',
        'pattern': None,
        'channel': 'ticker_00',
        'data': '{"name": "ticker_00", "price": 2, "created_at": "2022-04-03T00:00:00+00:00"}',
    }

    parsed = RedisPriceMessage.parse_obj(msg)

    assert parsed.type == 'message'
    assert parsed.payload.price == 2
    assert parsed.payload.created_at == datetime(year=2022, month=4, day=3, tzinfo=timezone.utc)
