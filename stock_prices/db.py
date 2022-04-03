from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm import declared_attr, sessionmaker

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

PK_TYPE = sa.BigInteger


class _Base:
    id = sa.Column(PK_TYPE, primary_key=True)


Base: 'TypeAlias' = so.as_declarative()(_Base)  # type: ignore


class Ticker(Base):
    __tablename__ = 'ticker'

    name = sa.Column(sa.Text, nullable=False, unique=True)

    prices = so.relationship('TickerPrice', back_populates='ticker', order_by=lambda: TickerPrice.id)

    @declared_attr
    def last_price(self) -> 'TickerPrice':  # type: ignore
        def condition():  # type: ignore
            aliased = so.aliased(TickerPrice, name='last_price')
            last_price_subquery = sa.select(
                [sa.func.max(so.remote(aliased.id))],
                whereclause=so.remote(aliased.ticker_id) == so.foreign(Ticker.id),
            ).scalar_subquery()

            ticker_id_condition = so.remote(TickerPrice.ticker_id) == so.foreign(Ticker.id)
            price_must_be_last = so.remote(TickerPrice.id) == last_price_subquery
            return ticker_id_condition & price_must_be_last

        return so.relationship('TickerPrice', primaryjoin=condition, uselist=False, viewonly=True)


class TickerPrice(Base):
    __tablename__ = 'ticker_price'

    ticker_id = sa.Column(sa.ForeignKey(Ticker.id), nullable=False, index=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True)
    price = sa.Column(sa.DECIMAL)

    ticker = so.relationship(Ticker, uselist=False, back_populates='prices', lazy='joined')


Session = sessionmaker()


@contextmanager
def create_session() -> Iterator[so.Session]:
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
