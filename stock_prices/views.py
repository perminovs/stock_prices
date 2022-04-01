import asyncio
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from typing import TYPE_CHECKING, Any

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


@lru_cache(maxsize=None)
def get_template() -> Jinja2Templates:
    return Jinja2Templates('static/templates')


def home(request: Request, templates: Jinja2Templates = Depends(get_template)) -> 'Response':
    with db.create_session() as session:
        tickers = session.query(db.Ticker).options(so.load_only(db.Ticker.name)).all()
        ticker_names = [t.name for t in tickers]

    return templates.TemplateResponse('home.html', {'request': request, 'tickers': ticker_names})


def get_ticker_price(ticker_name: str, limit: int = 15) -> list[TickerPrice]:
    with db.create_session() as session:
        last_prices: list[db.TickerPrice] = (
            session.query(db.TickerPrice)
            .join(db.Ticker, db.Ticker.id == db.TickerPrice.ticker_id)
            .filter(db.Ticker.name == ticker_name)
            .order_by(db.TickerPrice.id.desc())
            .limit(limit)
            .all()
        )
        return [TickerPrice(name=ticker_name, price=p.price, created_at=p.created_at) for p in reversed(last_prices)]


async def ticker_price(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        try:
            ticker_name, older_than = await websocket.receive_json()
        except WebSocketDisconnect:
            return

        # todo fix front-end
        last_prices = await asyncio.to_thread(_get_price_updates, ticker_name, older_than)
        await websocket.send_json(last_prices)


def _get_price_updates(ticker_name: str, older_than: datetime) -> list[dict[str, Any]]:
    with db.create_session() as session:
        last_prices: list[db.TickerPrice] = (
            session.query(db.TickerPrice)
            .join(db.Ticker, db.Ticker.id == db.TickerPrice.ticker_id)
            .filter(db.Ticker.name == ticker_name, db.TickerPrice.created_at > older_than)
            .order_by(db.TickerPrice.id.asc())
            .limit(1000)  # just in case of error, normally we do not expect front-end to ask for deep range
            .all()
        )
        return jsonable_encoder(
            [TickerPrice(name=ticker_name, price=p.price, created_at=p.created_at).dict() for p in last_prices]
        )
