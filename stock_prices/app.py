from typing import TYPE_CHECKING, Union

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from stock_prices.views import get_ticker_price, home, ticker_price

if TYPE_CHECKING:
    from pathlib import Path


def get_app(static_directory: Union[str, 'Path'] = 'static') -> FastAPI:
    app = FastAPI()

    origins = ['http://localhost', 'http://localhost:8000']  # todo settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.mount('/static', StaticFiles(directory=static_directory), name='static')

    app.get('/')(home)
    app.get('/ticker-price')(get_ticker_price)

    app.websocket('/track-price')(ticker_price)

    return app
