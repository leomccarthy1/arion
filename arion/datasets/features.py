import pandas as pd
import os
from arion.datasets import clean
import numpy as np
from typing import List


def draw_fts(df: pd.DataFrame) -> pd.DataFrame:
    df["draw_wins"] = df.groupby(["course", "draw", "distance_f"])["won"].apply(
        lambda x: x.cumsum().shift().fillna(0)
    )
    runs = df.groupby(["course", "draw", "distance_f"]).cumcount()
    df["draw_strike"] = (df["draw_wins"] / runs).fillna(0)

    return df


def exponentials(
    df: pd.DataFrame, groups: List[List[str]], features: List[str], halflife: int
):

    for group in groups:
        group_name = "_".join(group)
        feature_names = [f"{group_name}_{i}_ewm" for i in features]

        df[feature_names] = df.groupby(group)[features].apply(
            lambda x: x.ewm(halflife=halflife).mean().shift(1)
        )

    return df


def make_groups(entity: List[str]) -> List[List[str]]:
    groups = [entity]
    groups += [entity + ["course"]]
    if entity in [["trainer"], ["horse_name"]]:
        groups += [entity + ["going"]]
    if entity in [["horse_name"]]:
        groups += [entity + ["distance_f"]]

    return groups


def make_rating_stats(df: pd.DataFrame) -> pd.DataFrame:
    df["max_or"] = df.groupby("horse_name")["or"].apply(
        lambda x: np.fmax.accumulate(x).shift()
    )
    df["max_rpr"] = df.groupby("horse_name")["rpr"].apply(
        lambda x: np.fmax.accumulate(x).shift()
    )
    df["max_ts"] = df.groupby("horse_name")["ts"].apply(
        lambda x: np.fmax.accumulate(x).shift()
    )

    return df


def recode(df: pd.DataFrame, rm: List[str]):
    cat = df.drop(columns=rm).select_dtypes(include=["object"]).columns.tolist()
    for i in cat:
        df[i] = pd.factorize(df[i], sort=True)[0]

    df.loc[df.finish_pos > 10, "finish_pos"] = 10

    return df


def normalize_by_group(df: pd.DataFrame, by=str, on=List[str]):
    groups = df.groupby(by)[on]
    # computes group-wise mean/std,
    # then auto broadcasts to size of group chunk
    mean = groups.transform(np.nanmean)
    std = groups.transform(np.nanstd)
    return (df[mean.columns] - mean) / std


def race_std(df: pd.DataFrame, rm: List[str]):

    numeric = list(df.dtypes[df.dtypes == "float64"].index)
    numeric = [i for i in numeric if i not in rm]

    df = df.merge(
        normalize_by_group(df, "race_id", numeric),
        left_index=True,
        right_index=True,
        suffixes=("", "_race_std"),
    )
    return df



def last_race(df: pd.DataFrame) -> pd.DataFrame:
    for i in ["rpr", "or", "ts", "price", "ovr_btn", 'distance_f']:
        df[f"{i}_lto"] = df.groupby("horse_name")[i].apply(lambda x: x.shift(1))

    df["or_change"] = df["or"] - df["or_lto"]

    return df


def clean_strings(string: str, type: str = "str") -> str:

    return (
        string.strip()
        .replace(",", " ")
        .replace("'", "")
        .replace('"', "")
        .replace(")", "")
        .replace("(", "")
        .title()
        .replace(".", "")
    )


def add_betfair_prices(df: pd.DataFrame, odds: pd.DataFrame):

    odds["date"] = odds["time"].dt.date.astype('datetime64')

    odds.rename(columns={"selection_name": "horse_name"}, inplace=True)
    odds["horse_name"] = [clean_strings(i) for i in odds["horse_name"]]
    df = df.merge(
        odds[["date", "horse_name", "last_price"]],
        on=["date", "horse_name"],
        how="left",
    )

    temp = df[~df["last_price"].isna()]
    noise = (temp.last_price - temp.price) / temp.price
    u = np.random.random(df.shape[0] - temp.shape[0])
    noise = np.percentile(noise, (100 * u).tolist())
    df.loc[df["last_price"].isna(), "last_price"] = df.loc[
        df["last_price"].isna(), "price"
    ] + (noise * df.loc[df["last_price"].isna(), "price"])
    df.loc[df["last_price"] < 1.01, "last_price"] = 1.01

    return df


def make_features(df_race:pd.DataFrame, prices:pd.DataFrame = None):
    df_race["won"] = np.where(df_race["finish_pos"] == 1, 1, 0)

    
    df_race = draw_fts(df_race)
    df_race["placed"] = np.where(
        df_race["finish_pos"] <= np.ceil(df_race["runners"] * 0.3), 1, 0
    )
    df_race["pct_beaten"] = (df_race["runners"] - df_race["finish_pos"]) / (
        df_race["runners"] - 1
    )
    df_race["days_since_last"] = (
        (df_race["datetime"] - (df_race.groupby("horse_name")["datetime"].shift(1))).dt.days
    ).fillna(0)
    df_race["month"] = df_race["datetime"].dt.month


    df_race = make_rating_stats(df_race)
    df_race = exponentials(
        df_race,
        groups=make_groups(["trainer"])
        + make_groups(["jockey"])
        + make_groups(["trainer", "jockey"]),
        features=["prize", "ovr_btn", "won", "placed", "pct_beaten"],
        halflife=6,
    )
    df_race = exponentials(
        df_race,
        groups=make_groups(["horse_name"]),
        features=[
            "prize",
            "ovr_btn",
            "won",
            "placed",
            "rpr",
            "or",
            "ts",
            "pct_beaten"
        ],
        halflife=2,
    )
    df_race = exponentials(
        df_race,
        groups=[["trainer","month"]],
        features=[
            "prize",
            "ovr_btn",
            "won",
        ],
        halflife=10,
    )
    df_race = last_race(df_race)
    
    if prices is not None:
        df_race = add_betfair_prices(df_race, odds=prices)
    else:
        df_race['last_price'] = df_race['price']

    drop = [
        "course_id",
        "course",
        "jockey",
        "trainer",
        "ovr_btn",
        "prize",
        "comment",
        "placed",
        "horse_num",
        "ts",
        "rpr",
        "pct_beaten"
    ]
    df_race = df_race.drop(columns=drop)

    dont_std = [
        "race_id",
        "horse_name",
        "date",
        "datetime",
        "finish_pos",
        "won",
        "class",
        "price",
        "last_price",
        "distance_f",
    ]
    df_race = recode(df_race, rm=dont_std)
    df_race = race_std(df_race, rm=dont_std)

    return df_race



