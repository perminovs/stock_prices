import sqlalchemy as sa
from pydantic import BaseSettings

from stock_prices.db import Session


class DBSettings(BaseSettings):
    url: str = 'postgresql://postgres@localhost:5432/postgres'

    class Config:
        env_prefix = 'DB_'

    def setup(self, echo: bool = False) -> None:
        engine = sa.create_engine(url=self.url, echo=echo)
        Session.configure(bind=engine)


class RedisSettings(BaseSettings):
    url: str = 'redis://localhost:6379'
