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
        time_to_off = market_book.market_definition.market_time - datetime.utcnow()
        if (
            market_book.status == "OPEN"
            and market_book.market_definition.race_type == "Flat"
            and time_to_off < timedelta(hours=3) and time_to_off > timedelta(hours=2.5)
            and not market_book.inplay
        ):

            return True

    def process_market_book(self, market, market_book):
        print(
            market_book.market_definition.venue,
            market_book.market_definition.market_time,
        )
        model = pickle.load(open( "artifacts/trained_model.pkl", "rb"))
        racecard = pd.read_csv(f'data/racecards/processed/{datetime.today().strftime("%Y_%m_%d")}.csv')
        racecard.drop(columns = 'last_price', inplace = True)
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
        # bets = details.loc[details["last_price"] == min(details["last_price"])]
        card = racecard.merge(details[['horse_name','last_price']], on = 'horse_name')
        card = card.loc[card['last_price'] != 0]
        preds = model.make_bets(card,balance = 100)
        bets = preds.merge(names, on = 'horse_name')
        print(f"book={sum(bets['model_prob'])}")
        print(bets)
        bets = bets.loc[bets['bet'] == True,]

        for runner in market_book.runners:
            if runner.selection_id in list(bets["selection_id"]):
                runner_context = self.get_runner_context(
                    market.market_id, runner.selection_id, runner.handicap
                )
                if runner_context.trade_count == 0:
                    # lay at current best back price
                    price = get_price(runner.ex.available_to_back,1)
                    # create trade
                    trade = Trade(
                        market_book.market_id,
                        runner.selection_id,
                        runner.handicap,
                        self,
                    )
                    selection = bets.loc[bets['selection_id'] == runner.selection_id,]
                    # create order
                    order = trade.create_order(
                        side="BACK",
                        order_type=LimitOrder(price, selection['bet_size'].values[0]),
                        notes={"horse_name":selection['horse_name'].values[0]}
                    )
                    # place order for execution
                    market.place_order(order)

                    with open('data/bets/bets_placed.csv', 'a', encoding='UTF8') as f:
                        writer = csv.writer(f)
                        # writer.writerow(['time_placed',
                        #                 'race_time',
                        #                 'horse_name',
                        #                 'selection_id',
                        #                 'market_id',
                        #                 'price',
                        #                 'size'])
                        writer.writerow([order.date_time_created,
                                        market_book.market_definition.market_time,
                                        order.notes["horse_name"],
                                        order.selection_id,
                                        order.market_id,
                                        order.order_type.price,
                                        order.order_type.size])


    def process_orders(self, market, orders):
        # kill order if unmatched in market for greater than 2 seconds
        for order in orders:
            if order.status == OrderStatus.EXECUTABLE:
                if order.elapsed_seconds and order.elapsed_seconds > 60:
                    market.cancel_order(order)

    def process_closed_market(self, market, market_book) -> None:
        for order in market.blotter:
            if order.size_matched >= 0:
                with open('data/bets/bets_cleared.csv', 'a', encoding='UTF8') as f:
                            writer = csv.writer(f)
                            # writer.writerow(['placed time',
                            #                 'race_time',
                            #                 'horse_name',
                            #                 'selection_id',
                            #                 'market_id',
                            #                 'price',
                            #                 'price_matched',
                            #                 'size',
                            #                 'size_matched',
                            #                 'profit'])
                            writer.writerow([order.date_time_created,
                                            market_book.market_definition.market_time,
                                            order.notes["horse_name"],
                                            order.selection_id,
                                            order.market_id,
                                            order.order_type.price,
                                            order.average_price_matched,
                                            order.order_type.size,
                                            order.size_matched,
                                            order.simulated.profit])



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

