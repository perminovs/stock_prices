from random import random
from typing import TYPE_CHECKING, Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.websockets import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from starlette.responses import Response

templates = Jinja2Templates('static/templates')
StockPriceType = tuple[int, int]


def home(request: Request) -> 'Response':
    tickers = ['ticker_01', 'ticker_02', 'ticker_03', 'ticker_04']
    return templates.TemplateResponse('home.html', {'request': request, 'tickers': tickers})


def get_ticker_price(ticker_name: str) -> Optional[list[StockPriceType]]:
    tickers = {
        'ticker_01': list(enumerate([1, 2, 3, 2, 1, 2, 2])),
        'ticker_02': list(enumerate([4, 5, 2, 1, 6, 4, 2])),
        'ticker_03': list(enumerate([0, 2, -1, -1, 2])),
        'ticker_04': list(enumerate([3, 3, 2, 1, 2, 1, 2])),
    }
    return tickers.get(ticker_name)


def get_ticker_list() -> list[str]:
    return ['ticker_01', 'ticker_02']


def generate_movement() -> int:
    return -1 if random() < 0.5 else 1


async def ticker_price(websocket: WebSocket) -> None:
    await websocket.accept()
    current_price, updated = 0, 0
    while True:
        try:
            await websocket.receive_text()
        except WebSocketDisconnect:
            return
        current_price += generate_movement()
        updated += 1
        await websocket.send_json({'price': current_price, 'updated': updated})
