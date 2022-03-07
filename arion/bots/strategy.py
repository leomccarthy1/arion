import flumine
import betfairlightweight
from betfairlightweight import StreamListener
from dotenv import load_dotenv
from flumine import Flumine, clients, BaseStrategy
from flumine.order.trade import Trade
from flumine.order.order import OrderStatus
from flumine.order.ordertype import LimitOrder
from flumine.utils import get_price
import os

from matplotlib.cbook import print_cycles


class BetPlacer(BaseStrategy):
    def check_market_book(self, market, market_book):
        if market_book.status != "CLOSED":
            return True


    def process_market_book(self, market, market_book):
        prices = {
            r.selection_id:r.ex.available_to_back[0]['price']
            for r in market_book.runners
            if r.status == "ACTIVE" 
        }
        print(prices)
        print([runner.runner_name for runner in market.market_catalogue.runners])
    
