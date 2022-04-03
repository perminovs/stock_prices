import asyncio
import json
import time
from random import random
from typing import Callable, Type

import sqlalchemy as sa
import sqlalchemy.orm as so
import typer

import stock_prices.settings
from stock_prices import db
from stock_prices.models import TickerPrice
from stock_prices.views import get_redis

app = typer.Typer()


@app.command()
def generate_prices(interval: int = 1) -> None:
    stock_prices.settings.DBSettings().setup()

    while True:
        start_time = time.monotonic()
        _update_prices(price_diff_generator=generate_movement)
        typer.secho('Generated prices')
        time.sleep(interval - (time.monotonic() - start_time))


def _update_prices(price_diff_generator: Callable[[], int], publish: bool = True) -> None:
    with db.create_session() as session:
        last_price: Type[db.TickerPrice] = so.aliased(db.TickerPrice)
        price_after_last: Type[db.TickerPrice] = so.aliased(db.TickerPrice)
        last_prices = (
            session.query(last_price)
            .outerjoin(
                price_after_last,
                sa.and_(
                    price_after_last.ticker_id == last_price.ticker_id,
                    price_after_last.created_at > last_price.created_at,
                ),
            )
            .filter(price_after_last.id.is_(None))
        )
        for last_price in last_prices.all():
            new_price = last_price.price + price_diff_generator()
            new_ticker_price = db.TickerPrice(ticker=last_price.ticker, price=new_price)
            session.add(new_ticker_price)
            session.flush()

            if publish:
                price_message = TickerPrice(
                    name=last_price.ticker.name,
                    price=new_price,
                    created_at=new_ticker_price.created_at,
                )
                asyncio.run(_publish(last_price.ticker.name, price_message))


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
            ticker = db.Ticker(name=f'ticker_{ticker_num}')
            ticker_price = db.TickerPrice(ticker=ticker, price=0)
            session.add_all((ticker, ticker_price))
