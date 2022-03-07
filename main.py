import os 
from dotenv import load_dotenv
import betfairlightweight
from arion.bots.strategy import BetPlacer
from betfairlightweight.filters import streaming_market_filter, streaming_market_data_filter
from flumine import Flumine, clients
from betfairlightweight.resources import MarketCatalogue
from flumine.markets.middleware import Middleware

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
strategy = BetPlacer( market_filter=streaming_market_filter(
        event_type_ids=["7"],
        country_codes=["GB"],
        market_types=["WIN"],
    )
)
framework.add_strategy(strategy)

framework.run()

