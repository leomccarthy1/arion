import pandas as pd
import numpy as np


class RaceDataTransformer:
    def __init__(self) -> None:
        pass


    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
        df = df.sort_values(by = 'datetime')

        df['rating_band'] = df['rating_band'].fillna('none_handicap')

        df = self.fill_runners(df)

        none_finish = [not i.strip().isnumeric() for i in df['finish_pos']]
        df['finish_pos'] =  np.where(none_finish, df['runners'], df['finish_pos']).astype('int8')      

        return df

    @staticmethod
    def fill_runners(df: pd.DataFrame) -> pd.DataFrame:
        runners = df.groupby('race_id')['horse_name'].transform('count')

        df['runners'] = df['runners'].fillna(runners)

        return df

        


