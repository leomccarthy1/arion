import os

import betfairlightweight
from betfairlightweight.filters import (streaming_market_data_filter,
                                        streaming_market_filter)
from betfairlightweight.resources import MarketCatalogue
from dotenv import load_dotenv
from flumine import Flumine, clients
from flumine.markets.middleware import Middleware

from arion.bots.strategy import BetPlacer

load_dotenv()

trading = betfairlightweight.APIClient(
    os.getenv("BFAIR_USERNAME"),
    os.getenv("BFAIR_PASSWORD"),
    app_key=os.getenv("BFAIR_KEY"),
    certs="arion/certs",
)
trading.betting.read_timeout = 30
client = clients.BetfairClient(trading, paper_trade=True)
framework = Flumine(client=client)
strategy = BetPlacer(
    market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB"],
        market_types=["WIN"],
    )
)
framework.add_strategy(strategy)

framework.run()
