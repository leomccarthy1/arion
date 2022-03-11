import pandas as pd
import numpy as np


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df = df.sort_values(by = 'datetime')
    df.insert(2,'date',df['datetime'].dt.date.astype("datetime64"))

    df = df.loc[~df['draw'].isna()]

    df['rating_band'] = df['rating_band'].fillna('none_handicap')

    df = fill_runners(df)

    none_finish = [not str(i).strip().isnumeric() for i in df['finish_pos']]
    df['finish_pos'] =  np.where(none_finish, df['runners'], df['finish_pos']).astype('int8')    

    df = df.loc[~df['horse_num'].isin(['NR','Nr','nr'])]  

    return df


def fill_runners(df: pd.DataFrame) -> pd.DataFrame:
    runners = df.groupby('race_id')['horse_name'].transform('count')

    df['runners'] = df['runners'].fillna(runners)

    return df

        
