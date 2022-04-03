import logging

import sqlalchemy as sa
from pydantic import BaseSettings, validator

from stock_prices.db import Session


class LoggingSetting(BaseSettings):
    format: str = '[%(asctime)s] <%(levelname)s> %(message)s'
    level: str = 'INFO'

    @validator('level', pre=True)
    def check_level(cls, value: str) -> str:  # noqa: N805
        if value not in logging._nameToLevel:
            raise ValueError(f'Incorrect logging level, should be one of {logging._nameToLevel.keys()}')
        return value

    def setup(self) -> None:
        logging.basicConfig(level=self.level, format=self.format)

    class Config:
        env_prefix = 'LOGGING_'


class CORSSettings(BaseSettings):
    enabled: bool = True
    origins: list[str] = ['http://localhost', 'http://localhost:8000']

    class Config:
        env_prefix = 'CORS'


class DBSettings(BaseSettings):
    url: str = 'postgresql://postgres@localhost:5432/postgres'

    class Config:
        env_prefix = 'DB_'

    def setup(self, echo: bool = False) -> None:
        engine = sa.create_engine(url=self.url, echo=echo)
        Session.configure(bind=engine)


class RedisSettings(BaseSettings):
    url: str = 'redis://localhost:6379'

    class Config:
        env_prefix = 'REDIS_'
