





def update(df:pd.DataFrame, raw_data_folder:str = 'data'):
    need_from = (datetime.strptime(df["date"].max(), '%Y-%m-%d')- timedelta(3)).strftime('%Y/%m/%d')
    recent = (datetime.now() - timedelta(1)).strftime('%Y/%m/%d')
    
    dateRange = need_from +'-'+recent
    print('Adding reults for ' + dateRange)

    results.scrape_races(dateRange, folder = folder)

    to_add = pd.read_csv(f"folder/{dateRange.replace('/', '_')}.csv")
    
    to_add = to_add.loc[to_add["type"] == "Flat"]


    to_add.set_index(["date","horse_name"], inplace = True)
    df.set_index(["date","horse_name"], inplace = True)


    df = pd.concat([df[~df.index.isin(to_add.index)], to_add]).reset_index()

    return df


def main():
    if update:
        current = pd.read_csv('data/cleaned.csv')

    