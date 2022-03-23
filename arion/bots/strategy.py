from datetime import datetime, timedelta
import pandas as pd
from flumine import BaseStrategy
from flumine.order.order import OrderStatus
from flumine.order.ordertype import LimitOrder
from flumine.order.trade import Trade
import pickle
import csv
import logging
from flumine.utils import get_price

logging.basicConfig(level=logging.ERROR)


class BetPlacer(BaseStrategy):
    def check_market_book(self, market, market_book):
        time_to_off = market_book.market_definition.market_time - datetime.now()
        if (
            market_book.status == "OPEN"
            and market_book.market_definition.race_type != "Flat"
            and time_to_off < timedelta(hours=6)
            and not market_book.inplay
        ):
            return True

    def process_market_book(self, market, market_book):
        print(
            market_book.market_definition.venue,
            market_book.market_definition.market_time,
        )
        # model = pickle.load(open( "artifacts/trained_model.pkl", "rb"))
        # racecard = pd.read_csv(f'data/racecards/processed/{datetime.today().strftime("%Y_%m_%d")}.csv')
        # racecard.drop(columns = 'last_price', inplace = True)
        prices = pd.DataFrame(
            [
                {
                    "selection_id": r.selection_id,
                    "last_price": r.ex.available_to_back[1]["price"],
                    "handicap": r.handicap,
                }
                for r in market_book.runners
                if r.status == "ACTIVE"
            ]
        )
        for runner in market_book.runners:
            runner_context = self.get_runner_context(
                market.market_id, runner.selection_id, runner.handicap
            )

        names = pd.DataFrame(
            [
                {
                    "selection_id": r.selection_id,
                    "horse_name": clean_strings(r.runner_name),
                }
                for r in market.market_catalogue.runners
            ]
        )
        details = prices.merge(names, on="selection_id")
        bets = details.loc[details["last_price"] == min(details["last_price"])]
        # card = racecard.merge(details[['horse_name','last_price']], on = 'horse_name')
        # card = card.loc[card['last_price'] != 0]
        # preds = model.make_bets(card)
        # bets = preds.merge(names, on = 'horse_name')
        # bets = bets.loc[bets['bet'] == True,]

        for runner in market_book.runners:
            if runner.selection_id in list(bets["selection_id"]):
                runner_context = self.get_runner_context(
                    market.market_id, runner.selection_id, runner.handicap
                )
                print(runner_context.trade_count)

                if runner_context.trade_count == 0:
                    # lay at current best back price
                    price = get_price(runner.ex.available_to_back, 1)
                    # create trade
                    trade = Trade(
                        market_book.market_id,
                        runner.selection_id,
                        runner.handicap,
                        self,
                    )
                    # size = bets.loc[bets['selection_id'] == runner.selection_id,"bet_size"][0]
                    print(bets)
                    name =  bets.loc[bets['selection_id'] == runner.selection_id,"horse_name"][0]
                    # create order
                    order = trade.create_order(
                        side="BACK",
                        order_type=LimitOrder(price, 1),
                        notes={"horse_name":name,"bet_size":1}
                    )
                    # place order for execution
                    print(order.json())
                    market.place_order(order)

                    with open('bets.csv', 'w', encoding='UTF8', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([order.notes["horse_name"],
                                        order.selection_id,
                                        order.market_id,
                                        order.average_price_matched,
                                        order.notes["bet_size"],
                                        order.size_matched,
                                        order.date_time_created])


    def process_orders(self, market, orders):
        # kill order if unmatched in market for greater than 2 seconds
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.elapsed_seconds and order.elapsed_seconds > 2:
                    market.cancel_order(order)

    def process_closed_market(self, market, market_book) -> None:
        for order in market.blotter:
            print(order.cleared_order.profit, order.selection_id,order.market_id,order.notes["horse_name"],order.size_matched)


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

