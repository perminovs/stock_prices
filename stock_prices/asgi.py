from stock_prices.app import get_app
from stock_prices.settings import DBSettings

DBSettings().setup()
app = get_app()
