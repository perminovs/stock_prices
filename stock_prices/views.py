import asyncio
import enum
import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any, cast

import aioredis
import sqlalchemy.orm as so
from aioredis import Redis, RedisError
from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from starlette.websockets import WebSocket
from websockets.exceptions import WebSocketException

from stock_prices import db
from stock_prices.models import RedisPriceMessage, TickerPrice
from stock_prices.settings import RedisSettings

if TYPE_CHECKING:
    from aioredis.client import PubSub
    from starlette.responses import Response

logger = logging.getLogger(__name__)


class WebSocketCloseCode(int, enum.Enum):
    INTERNAL_ERROR = 1011
    TRY_AGAIN_LATER = 1013


@lru_cache(maxsize=None)
def get_template() -> Jinja2Templates:
    return Jinja2Templates('static/templates')


async def get_redis() -> 'Redis':
    settings = RedisSettings()
    return aioredis.from_url(settings.url, decode_responses=True)


def home(request: Request, templates: Jinja2Templates = Depends(get_template)) -> 'Response':
    with db.create_session() as session:
        tickers = session.query(db.Ticker).options(so.load_only(db.Ticker.name)).all()
        ticker_names = [t.name for t in tickers]

    return templates.TemplateResponse('home.html', {'request': request, 'tickers': ticker_names})


def get_ticker_price(ticker_name: str) -> list[TickerPrice]:
    with db.create_session() as session:
        last_prices: list[db.TickerPrice] = (
            session.query(db.TickerPrice)
            .join(db.Ticker, db.Ticker.id == db.TickerPrice.ticker_id)
            .filter(db.Ticker.name == ticker_name)
            .order_by(db.TickerPrice.id.desc())
            .all()
        )
        return [TickerPrice(name=ticker_name, price=p.price, created_at=p.created_at) for p in reversed(last_prices)]


async def ticker_price(websocket: 'WebSocket', redis: 'Redis' = Depends(get_redis)) -> None:
    await websocket.accept()

    ticker_name = await websocket.receive_text()
    logger.info('Start tracking price updates for %s', ticker_name)

    async with redis.pubsub() as reader:
        await reader.subscribe(ticker_name)
        await listen_to_updates(reader, websocket, ticker_name)


async def _get_message(reader: 'PubSub') -> dict[str, Any]:
    return await reader.get_message()


async def listen_to_updates(reader: 'PubSub', websocket: 'WebSocket', ticker_name: str) -> None:
    while True:
        try:
            raw_message = await _get_message(reader)
        except RedisError:
            logging.exception('Cannot read from redis, stop tracking ticker %s', ticker_name)
            await websocket.close(code=WebSocketCloseCode.TRY_AGAIN_LATER)
            break

        if not raw_message:
            await asyncio.sleep(0.1)
            continue

        try:
            message = RedisPriceMessage.parse_obj(raw_message)
        except ValueError:
            logging.exception('Cannot parse redis price info, stop tracking ticker %s', ticker_name)
            await websocket.close(code=WebSocketCloseCode.INTERNAL_ERROR)
            break
        if message.type != 'message':
            await asyncio.sleep(0.1)
            continue

        price_info = cast(TickerPrice, message.payload).encoded()
        try:
            await websocket.send_json(price_info)
        except WebSocketException:
            logger.info('Cannot send to websocket, stop tracking ticker %s', ticker_name)
            await reader.unsubscribe(ticker_name)
            break
