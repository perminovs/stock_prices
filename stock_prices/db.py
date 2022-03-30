from contextlib import contextmanager
from typing import Iterator

import sqlalchemy as sa
import sqlalchemy.orm as so
from pydantic import BaseSettings
from sqlalchemy.orm import sessionmaker

PK_TYPE = sa.BigInteger


class _Base:
    id = sa.Column(PK_TYPE, primary_key=True)


Base = so.as_declarative()(_Base)


class Ticker(Base):
    __tablename__ = 'ticker'

    name = sa.Column(sa.Text, nullable=False, index=True)

    prices = so.relationship('TickerPrice', back_populates='ticker')


class TickerPrice(Base):
    __tablename__ = 'ticker_price'

    ticker_id = sa.Column(sa.ForeignKey(Ticker.id), nullable=False, index=True)
    price = sa.Column(sa.Integer)  # TODO as TEXT

    ticker = so.relationship(Ticker, uselist=False, back_populates='prices')


Session = sessionmaker()


class DBSettings(BaseSettings):
    url: str = 'sqlite:///tickers.db'

    class Config:
        env_prefix = 'DB_'

    def setup(self):
        engine = sa.create_engine(url=self.url)
        Session.configure(bind=engine)


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
