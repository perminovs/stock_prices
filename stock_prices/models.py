import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, validator


class TickerPrice(BaseModel):
    name: str
    price: Decimal
    created_at: datetime

    def encoded(self) -> dict[str, Any]:
        return jsonable_encoder(self.dict())


class RedisPriceMessage(BaseModel):
    type: str
    payload: Optional[TickerPrice] = Field(None, alias='data')

    @validator('payload', pre=True, whole=True)
    def load_data(cls, value: str, values: dict[str, Any]) -> Optional[dict[str, Any]]:  # noqa: N805
        if values['type'] != 'message':
            return None
        return json.loads(value)
