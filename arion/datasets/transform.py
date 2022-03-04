from unittest import result
import pandas as pd

class RaceDataTransformer:
    def __init__(self) -> None:
        pass
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        df.sort_values(by = 'datetime', inplace = True)

        df['rating_band'] = df['rating_band'].fillna('none_handicap')

        df = self.fill_runners(df)

        return df

    @staticmethod
    def fill_runners(df: pd.DataFrame):
        runners = df.groupby('race_id')['horse_name'].transform('count')

        df['runners'] = df['runners'].fillna(runners)

        return df


