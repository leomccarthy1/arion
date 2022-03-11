from arion.models.core import ArionModel
import pandas as pd
import pickle

def main():
    train = pd.read_csv('data/results/processed/results_processed.csv', parse_dates=['date','datetime'])
    not_features = ['race_id','date','datetime','won','price','horse_name','finish_pos']
    model = ArionModel()

    model = ArionModel(not_features=not_features)
    model.train(train=train)

    pickle.dump(model,open( "artifacts/trained_model.pkl", "wb"))


if __name__ == "__main__":
    main()