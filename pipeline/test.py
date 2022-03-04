import pandas as pd
import os

filepaths = [f for f in os.listdir("data/results") if f.endswith(".csv")]
results = pd.concat([pd.read_csv(f"data/results/{i}", lineterminator='\n',parse_dates=['datetime'], infer_datetime_format = True) for i in filepaths])


def clean(df:pd.DataFrame) -> pd.DataFrame:
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df.sort_values(by = 'datetime', inplace = True)

    df['rating_band'] = df['rating_band'].fillna('none_handicap')

    return df




