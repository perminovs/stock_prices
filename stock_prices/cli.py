import asyncio
import json
import time
from random import random
from typing import Callable

import sqlalchemy.orm as so
import typer

import stock_prices.settings
from stock_prices import db
from stock_prices.models import TickerPrice
from stock_prices.views import get_redis

app = typer.Typer()


@app.command()
def generate_prices(interval: float = 1.0) -> None:
    stock_prices.settings.DBSettings().setup()

    while True:
        start_time = time.monotonic()
        _update_prices(price_diff_generator=generate_movement)
        typer.secho('Prices have been Generated')
        to_sleep = interval - (time.monotonic() - start_time)
        if to_sleep > 0:
            time.sleep(to_sleep)


def _update_prices(price_diff_generator: Callable[[], int], publish: bool = True) -> None:
    with db.create_session() as session:
        tickers: list[db.Ticker] = session.query(db.Ticker).options(so.joinedload(db.Ticker.last_price)).all()
        for ticker in tickers:
            new_price = 0
            if last_price := ticker.last_price:
                new_price = last_price.price + price_diff_generator()
            new_ticker_price = db.TickerPrice(ticker=ticker, price=new_price)
            session.add(new_ticker_price)
            session.flush()

            if publish:
                price_message = TickerPrice(
                    name=ticker.name,
                    price=new_price,
                    created_at=new_ticker_price.created_at,
                )
                asyncio.run(_publish(ticker.name, price_message))


def generate_movement() -> int:
    return -1 if random() < 0.5 else 1


async def _publish(ticker_name: str, price_message: TickerPrice) -> None:
    redis = await get_redis()
    message = json.dumps(price_message.encoded())
    await redis.publish(ticker_name, message)


@app.command()
def fill_db(amount: int = 100) -> None:
    stock_prices.settings.DBSettings().setup()

    with db.create_session() as session:
        for i in range(amount):
            ticker_num = str(i).rjust(2, '0')
            session.add(db.Ticker(name=f'ticker_{ticker_num}'))
