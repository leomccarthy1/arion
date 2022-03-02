import pandas as pd
import os
import betfairlightweight
from betfairlightweight import StreamListener
import os
import numpy as np
from typing import List
from dotenv import load_dotenv
from smart_open import smart_open
from tqdm import tqdm
from unittest.mock import patch
import smart_open 
from datetime import timedelta
from fire import Fire


class BetfairPrices:
    def __init__(self) -> None:
        load_dotenv()
        self.trading = betfairlightweight.APIClient(
        os.getenv("BFAIR_USERNAME"),
        os.getenv("BFAIR_PASSWORD"),
        app_key=os.getenv("BFAIR_KEY"),
        certs="/Users/leomccarthy/Documents/arion/certs",
        )

        self.listener = StreamListener(max_latency=None)

        self.trading.historic.read_timeout = 300
        self.trading.historic.connect_timeout = 50
        
        
    def make_prices(self,files: List[str]):
        self.trading.login()
        races = []
        for file in files:
            stream = self.trading.streaming.create_historical_generator_stream(
                file_path=file,
                listener=self.listener,
            )
            with patch("builtins.open", smart_open.open):   
                gen = stream.get_generator()
                runner_prices = []

                try:
                    for market_books in gen():
                        
                        for market_book in market_books:

                            market_def = market_book.market_definition
                            if (market_def.market_time - market_book.publish_time) <= timedelta(hours=3) and market_book.status == "OPEN":
                                runners_dict = {
                                                runner.selection_id:runner.name
                                                for runner in market_def.runners
                                            }
                                
                                for runner in market_book.runners:
                                        if runner.status == "ACTIVE":
                                            line_dict = {
                                                'time':market_book.publish_time,
                                                'off_time':market_def.market_time,
                                                'market_id':market_book.market_id,
                                                'status':market_book.status,
                                                'inplay':market_book.inplay,
                                                'selection_id':runner.selection_id,
                                                'selection_name':runners_dict[runner.selection_id],
                                                'last_price':runner.last_price_traded or ""
                                                }
                                            
                                        runner_prices.append(line_dict)
                except OSError:
                    continue
                                        
                prices = pd.DataFrame(runner_prices)
                if prices.empty:
                    continue
                prices.time = prices.time.astype("datetime64")
                prices.sort_values(by = 'time', inplace = True)
                match = np.searchsorted(prices.time,market_book.market_definition.market_time  - timedelta(hours=2))
                if match == 0:
                    match = 1
                match_time = prices.time[match-1]
                races.append(prices.loc[prices.time.astype("datetime64") == match_time,].drop_duplicates())
            
        all_races = pd.concat(races).sort_values(by="time")

        return all_races



def main(input_folder:str = "data/odds/betfair/2015", output_path:str = 'data/odds/two_hour/2015.csv'):
    streamer = BetfairPrices()
    files = [f"{input_folder}/{file}" for file in os.listdir(input_folder)]

    out = streamer.make_prices(files)

    out.to_csv(output_path, index = False)


if __name__ == "__main__":
    Fire(main)