from arion.scraping import scraper
from arion.datasets import features, clean
import pandas as pd
from datetime import datetime, timedelta, date
from fire import Fire

def update(df:pd.DataFrame):
    need_from = (df["date"].max() - timedelta(3)).strftime('%Y/%m/%d')
    recent = (datetime.now() - timedelta(1)).strftime('%Y/%m/%d')
    
    dateRange = need_from +'-'+recent
    print('Adding reults for ' + dateRange)

    folder = "data/results/updates"
    # scraper.scrape_races(dateRange, folder = folder)

    to_add = pd.read_csv(f"{folder}/{dateRange.replace('/', '_')}.csv", lineterminator='\n', parse_dates=['datetime'])
    
    to_add = to_add.loc[~to_add['draw'].isna()]
    to_add = clean.clean_data(to_add)
    df = pd.concat([df, to_add], ignore_index=True)

    return df


def main(scrape_card:bool = True, update_results:bool = True):
    results = pd.read_csv('data/results/processed/results_clean.csv', lineterminator='\n', parse_dates=['datetime','date'])
    if update_results:
        results = update(results)

    if scrape_card:
        scraper.scrape_racecard(day = 'today', folder = 'data/racecards/raw')
    
    day = datetime.today().strftime('%Y_%m_%d')
    card = pd.read_csv(f'data/racecards/raw/{day}.csv', parse_dates=['datetime'])
    card = card.loc[~card['draw'].isna()]
    card = clean.clean_data(card)

    combined = pd.concat([results,card],ignore_index=True).sort_values(by='datetime')

    processed = features.make_features(combined)
    processed_card = processed.loc[processed['date'] == day.replace("_","-")]
    processed_card.to_csv(f"data/racecards/processed/{day}.csv", index = False)


if __name__ == "__main__":
    Fire(main)
    