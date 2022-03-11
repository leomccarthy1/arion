import pandas as pd
from arion.scraping import scraper
from arion.datasets import features, clean
from datetime import datetime, timedelta
import os
from fire import Fire

def main(update:bool = False, build_features:bool = False):
    if update:
        clean_data = pd.read_csv('data/results/processed/results_clean.csv', parse_dates=['date'],lineterminator="\n")
        need_from = (clean_data["date"].max() + timedelta(days=1)).strftime('%Y/%m/%d')
        recent = (datetime.now() - timedelta(7)).strftime('%Y/%m/%d')
        
        if need_from <= recent:
            if need_from == recent:
                dateRange = need_from
            else:
                dateRange = need_from +'-'+recent

            scraper.scrape_races(dateRange, folder = 'data/results/raw')


    filepaths = [f for f in os.listdir("data/results/raw") if f.endswith(".csv")]
    results = pd.concat(
        [
            pd.read_csv(
                f"data/results/raw/{i}",
                lineterminator="\n",
                parse_dates=["datetime"],
                infer_datetime_format=True,
            )
            for i in filepaths
        ],
        ignore_index=True,
    )

    pricefiles = [f for f in os.listdir(f"data/odds/two_hour") if f.endswith(".csv")]
    prices = pd.concat(
        [pd.read_csv(f"data/odds/two_hour/{i}", parse_dates=["time"]) for i in pricefiles]
    )


    cleaned_data = clean.clean_data(results)
    cleaned_data.to_csv("data/results/processed/results_clean.csv",index = False)
    if build_features:
        processed_data = features.make_features(cleaned_data ,prices=prices)

        processed_data.to_csv("data/results/processed/results_processed.csv", index=False)

if __name__ == "__main__":
    Fire(main)