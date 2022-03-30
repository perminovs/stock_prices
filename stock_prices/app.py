from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from stock_prices.views import get_ticker_list, get_ticker_price, home, ticker_price


def get_app() -> FastAPI:
    app = FastAPI()

    origins = ['http://localhost', 'http://localhost:8000']
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.mount('/static', StaticFiles(directory='static'), name='static')

    app.get('/')(home)
    app.get('/tickers')(get_ticker_list)
    app.get('/ticker-price')(get_ticker_price)

    app.websocket('/track-price')(ticker_price)

    return app
