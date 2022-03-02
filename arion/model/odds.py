import betfairlightweight
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

trading = betfairlightweight.APIClient(
    os.getenv("BFAIR_USERNAME"),
    os.getenv("BFAIR_PASSWORD"),
    app_key=os.getenv("BFAIR_KEY"),
    certs="/Users/leomccarthy/Documents/arion/certs",
)
trading.login()

trading.historic.read_timeout = 300
trading.historic.connect_timeout = 50

for  year in [2015,2016,2017,2018,2019,2020,2021]:

    if year == 2015:
        month_start = 4
    else:
        month_start = 1
       
    file_list = trading.historic.get_file_list(
        "Horse Racing",
        "Basic Plan",
        from_day=1,
        from_month=month_start,
        from_year=year,
        to_day=31,
        to_month=12,
        to_year=year,
        market_types_collection=["WIN"],
        countries_collection=["GB"],
        file_type_collection=["M","E"],
    )

    if not os.path.exists(f"data/odds/betfair/{year}"):
        os.makedirs(f"data/odds/betfair/{year}")
        
    for file in tqdm(file_list):
        trading.historic.download_file(file_path=file,store_directory = f"data/odds/betfair/{year}")


