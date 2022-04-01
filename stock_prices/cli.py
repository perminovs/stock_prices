import time
from random import random
from typing import Type

import sqlalchemy as sa
import typer

from stock_prices import db

app = typer.Typer()


@app.command()
def generate_prices() -> None:
    db.DBSettings().setup()

    while True:
        start_time = time.monotonic()
        _update_prices()
        time.sleep(1 - (time.monotonic() - start_time))


def _update_prices() -> None:
    with db.create_session() as session:
        last_price: Type[db.TickerPrice] = sa.alias(db.TickerPrice)
        price_after_last: Type[db.TickerPrice] = sa.alias(db.TickerPrice)
        last_prices = (
            session.query(last_price)
            .join(db.Ticker, db.Ticker.id == last_price.ticker_id)
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
            new_price = last_price.price + 1 if random() > 0.5 else -1
            session.add(db.TickerPrice(ticker=last_price.ticker, price=new_price))


@app.command()
def fill_db() -> None:
    db.DBSettings().setup()

    with db.create_session() as session:
        for i in range(10):
            ticker_num = str(i).rjust(2, '0')
            ticker = db.Ticker(name=f'ticker_{ticker_num}')
            ticker_price = db.TickerPrice(ticker=ticker, price=0)
            session.add_all((ticker, ticker_price))
