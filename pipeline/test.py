import pandas as pd
import os
from arion.datasets.transform import RaceDataTransformer

filepaths = [f for f in os.listdir("data/results") if f.endswith(".csv")]
results = pd.concat([pd.read_csv(f"data/results/{i}", lineterminator='\n',parse_dates=['datetime'], infer_datetime_format = True) for i in filepaths])

transformer = RaceDataTransformer()

print(transformer.clean(results))

