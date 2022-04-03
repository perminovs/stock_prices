from stock_prices.app import get_app
from stock_prices.settings import DBSettings, LoggingSetting

LoggingSetting().setup()
DBSettings().setup()
app = get_app()
