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
import pickle

from arion.scraping import racecard


class BetPlacer(BaseStrategy):

    def check_market_book(self, market, market_book):
        time_to_off = market_book.market_definition.market_time - datetime.now()
        if market_book.status != "CLOSED" and  market_book.market_definition.race_type == "Flat" and time_to_off < timedelta(hours=18):
            return True

    def process_market_book(self, market, market_book):
        print(market_book.market_definition.race_type)
        model = pickle.load(open( "artifacts/trained_model.pkl", "rb"))
        racecard = pd.read_csv(f'data/racecards/processed/{datetime.today().strftime("%Y_%m_%d")}.csv')
        racecard.drop(columns='last_price', inplace = True)
        
        prices = pd.DataFrame(
            [
                {
                    "selection_id": r.selection_id,
                    "last_price": r.ex.available_to_back[1]["price"],
                }
                for r in market_book.runners
                if r.status == "ACTIVE"
            ]
        )
        print(prices)
        names = pd.DataFrame(
            [
                {"selection_id": runner.selection_id, "horse_name": clean_strings(runner.runner_name)}
                for runner in market.market_catalogue.runners
            ]
        )
        details = prices.merge(names, on='selection_id')
        preds = model.make_bets(racecard.merge(details[['horse_name','last_price']], on = 'horse_name'))
        bets = preds.merge(names, on = 'horse_name')

        for index, row in bets.iterrows():
            if row["bet"] == True:
                trade = Trade(
                    market_id=market_book.market_id, 
                    selection_id=row["selection_id"],
                    strategy=self
                )
                order = trade.create_order(
                    side="BACK", 
                    order_type=LimitOrder(price=row['last_price'], size=row["bet_size"])
                )
                market.place_order(order)
    
    
    def process_orders(self, market, orders: list) -> None:
        # kill order if unmatched in market for greater than 2 seconds
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.elapsed_seconds and order.elapsed_seconds > 2:
                    market.cancel_order(order)





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
