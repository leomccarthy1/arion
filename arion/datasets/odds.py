import os
from datetime import timedelta
from typing import List
from unittest.mock import patch
from datetime import datetime
import betfairlightweight
import numpy as np
import pandas as pd
import smart_open
from betfairlightweight import StreamListener
from dotenv import load_dotenv
from fire import Fire
import smart_open
from tqdm import tqdm

class BetfairPrices:
    def __init__(self) -> None:
        load_dotenv()
        self.trading = betfairlightweight.APIClient(
            os.getenv("BFAIR_USERNAME"),
            os.getenv("BFAIR_PASSWORD"),
            app_key=os.getenv("BFAIR_KEY"),
            certs="arion/certs",
        )


        self.listener = StreamListener(max_latency=None)

        self.trading.historic.read_timeout = 300
        self.trading.historic.connect_timeout = 50

    def download(self, years: List[int], output_path: str):
        for year in years:

            if year == 2015:
                month_start = 4
            else:
                month_start = 1
            if year == 2022:
                month_end = datetime.now().month - 1
            else:
                month_end = 12
            
            self.trading.login()
            file_list = self.trading.historic.get_file_list(
                "Horse Racing",
                "Basic Plan",
                from_day=1,
                from_month=month_start,
                from_year=year,
                to_day=28,
                to_month=month_end,
                to_year=year,
                market_types_collection=["WIN"],
                countries_collection=["GB"],
                file_type_collection=["M"],
            )

            if not os.path.exists(f"{output_path}/{year}"):
                os.makedirs(f"{output_path}/{year}")

            for file in tqdm(file_list):
                self.trading.historic.download_file(
                    file_path=file, store_directory=f"{output_path}/{year}"
                )

    def make_prices(self, files: List[str]):
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
                            if (
                                market_def.market_time - market_book.publish_time
                            ) <= timedelta(hours=3) and market_book.status == "OPEN":
                                runners_dict = {
                                    runner.selection_id: runner.name
                                    for runner in market_def.runners
                                }

                                for runner in market_book.runners:
                                    if runner.status == "ACTIVE":
                                        line_dict = {
                                            "time": market_book.publish_time,
                                            "off_time": market_def.market_time,
                                            "market_id": market_book.market_id,
                                            "status": market_book.status,
                                            "inplay": market_book.inplay,
                                            "selection_id": runner.selection_id,
                                            "selection_name": runners_dict[
                                                runner.selection_id
                                            ],
                                            "last_price": runner.last_price_traded
                                            or "",
                                        }

                                    runner_prices.append(line_dict)
                except OSError:
                    continue

                prices = pd.DataFrame(runner_prices)
                if prices.empty:
                    continue
                prices.time = prices.time.astype("datetime64")
                prices.sort_values(by="time", inplace=True)
                match = np.searchsorted(
                    prices.time,
                    market_book.market_definition.market_time - timedelta(hours=1),
                )
                if match == 0:
                    match = 1
                match_time = prices.time[match - 1]
                races.append(
                    prices.loc[
                        prices.time.astype("datetime64") == match_time,
                    ].drop_duplicates()
                )

        all_races = pd.concat(races).sort_values(by="time")

        return all_races


def main(
    years: List[int],
    mode: str = "transform",
    download_folder: str = "data/odds/betfair",
    output_folder: str = "data/odds/one_hour",
):
    streamer = BetfairPrices()

    if mode == "download":
        streamer.download(years, output_path=download_folder)

    if mode == 'transform':
        for year in years:
            files = [f"{download_folder}/{year}/{file}" for file in os.listdir(f"{download_folder}/{year}")]
            out = streamer.make_prices(files)
            out.to_csv(f"{output_folder}/{year}.csv", index=False)


if __name__ == "__main__":
    Fire(main)
