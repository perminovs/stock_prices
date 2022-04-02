import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Optional

import sqlalchemy.orm as so
from fastapi import Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.websockets import WebSocket, WebSocketDisconnect

from stock_prices import db

if TYPE_CHECKING:
    from starlette.responses import Response


class TickerPrice(BaseModel):
    name: str
    price: Decimal
    created_at: datetime


UPDATE_INTERVAL = timedelta(seconds=1)  # TODO as env
PRICE_DEEP = 15  # todo here or front-end?


@lru_cache(maxsize=None)
def get_template() -> Jinja2Templates:
    return Jinja2Templates('static/templates')


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


async def ticker_price(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        ticker_name = await websocket.receive_text()
        print(f'listening to changes of {ticker_name = }')
    except WebSocketDisconnect:
        return

    previous = None
    while True:
        last_prices = await asyncio.to_thread(_get_last_price, ticker_name)
        if previous and previous.created_at <= last_prices.created_at:
            continue
        try:
            await websocket.send_json(jsonable_encoder(last_prices.dict()))
        except WebSocketDisconnect:
            return
        await asyncio.sleep(UPDATE_INTERVAL.total_seconds())
        previous = last_prices


def _get_last_price(ticker_name: str) -> Optional[TickerPrice]:
    with db.create_session() as session:
        last_price: Optional[db.TickerPrice] = (
            session.query(db.TickerPrice)
            .join(db.Ticker, db.Ticker.id == db.TickerPrice.ticker_id)
            .filter(db.Ticker.name == ticker_name)
            .order_by(db.TickerPrice.id.desc())
            .limit(1)
            .first()
        )
        print(f'{last_price.ticker.name = }, {last_price.price = }, {last_price.created_at = }')
        if not last_price:
            return None
        return TickerPrice(name=ticker_name, price=last_price.price, created_at=last_price.created_at)
