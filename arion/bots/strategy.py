import os
from datetime import datetime, timedelta

import betfairlightweight
import flumine
import pandas as pd
from betfairlightweight import StreamListener
from dotenv import load_dotenv
from flumine import BaseStrategy, Flumine, clients
from flumine.order.order import OrderStatus
from flumine.order.ordertype import LimitOrder
from flumine.order.trade import Trade
from flumine.utils import get_price
from matplotlib.cbook import print_cycles


class BetPlacer(BaseStrategy):
    def check_market_book(self, market, market_book):
        time_to_off = market_book.market_definition.market_time - datetime.now()
        if market_book.status != "CLOSED" and time_to_off < timedelta(hours=8):
            return True

    def process_market_book(self, market, market_book):
        prices = pd.DataFrame(
            [
                {
                    "selection_id": r.selection_id,
                    "price": r.ex.available_to_back[0]["price"],
                }
                for r in market_book.runners
                if r.status == "ACTIVE"
            ]
        )
        names = pd.DataFrame(
            [
                {"selection_id": runner.selection_id, "horse_name": runner.runner_name}
                for runner in market.market_catalogue.runners
            ]
        )


def clean_strings(string: str, type: str = "str") -> str:

    return (
        string.strip()
        .replace(",", " ")
        .replace("'", "")
        .replace('"', "")
        .replace(")", "")
        .replace("(", "")
        .title()
        .replace(".", "")
        .replace("\x80", "")
        .replace("\\x80", "")
        .replace("\xa0", " ")
        .replace("\n", " ")
        .replace("      ", "")
        .replace("\r", "")
    )
