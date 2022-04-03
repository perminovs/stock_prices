from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm import sessionmaker

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
