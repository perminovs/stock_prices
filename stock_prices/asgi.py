from stock_prices.app import get_app
from stock_prices.db import DBSettings

DBSettings().setup()
app = get_app()
