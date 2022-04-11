import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from typing import List

class ArionModel:
    def __init__(self,not_features:List[str] = None) -> None:
        self.params =  {
                        'boost_from_average':False,
                        'num_leaves': 64,
                        'objective': 'binary',
                        'num_threads': 7,
                        'eta': 0.02,
                        'bagging_fraction': 0.9,
                        'bagging_freq': 2,
                        'max_depth': 16,
                        "lambda_l2":0,
                        "drop_rate":0.3,
                        'min_data_in_leaf': 3000,
                        "metric":'binary_logloss',
                        'force_col_wise':True
                        }
        self.rank_params = {
                    'boost_from_average':False,
                    'num_leaves': 64,
                    'objective': 'lambdarank',
                    'num_threads': 7,
                    'eta': 0.02,
                    'bagging_fraction': 0.9,
                    'bagging_freq': 4,
                    'max_depth': 12,
                    "lambda_l2":0,
                    "drop_rate":0,
                    'min_data_in_leaf': 3000,
                    'force_col_wise':True
                    }
        self.not_features = not_features


    def get_oof(self,train = pd.DataFrame):
        y = train['finish_pos']

        skf = StratifiedKFold(n_splits=4)
        oof = np.zeros(len(train))

        callbacks = [lgb.log_evaluation(period=0)]

        for train_index, test_index in skf.split(train,y):
            X_train, X_val = train.iloc[train_index], train.iloc[test_index]
            y_train_rank, y_val_rank = y.iloc[train_index], y.iloc[test_index]
            
            q_train = X_train["race_id"].value_counts()[X_train["race_id"].unique()]
            q_val = X_val["race_id"].value_counts()[X_val["race_id"].unique()]

            X_train = X_train.drop(columns=self.not_features)
            X_val = X_val.drop(columns=self.not_features)

            dtrain = lgb.Dataset(X_train,label = y_train_rank,free_raw_data=False,
                                    group = q_train)
            dval = lgb.Dataset(X_val,label = y_val_rank,free_raw_data=False,
                                    group = q_val,reference=dtrain)
            
            model = lgb.train(self.rank_params,
                            dtrain,
                            valid_sets=[dtrain, dval],
                            num_boost_round=200,
                            callbacks = callbacks
                        )
            
            y_pred = -model.predict(X_val)    
            oof[test_index] = y_pred

        return oof
    
    def train(self, train: pd.DataFrame):
        q_train = train["race_id"].value_counts()[train["race_id"].unique()]
        y_rank = train['finish_pos']
        y = train['won']

        dtrain = lgb.Dataset(train.drop(columns=self.not_features),label = y_rank,free_raw_data=False,
                            group = q_train)

        
        self.lgbst_rank = lgb.train(self.rank_params,
                            dtrain,
                            num_boost_round=200
                        )

        train["rank"] = self.get_oof(train)
        train["prob"] = train[["race_id","rank"]].groupby("race_id")["rank"].apply(lambda x: np.exp(x)/sum(np.exp(x)))

        dtrain = lgb.Dataset(train.drop(columns=self.not_features),label = y,free_raw_data=False)

        self.lgbst = lgb.train(train_set = dtrain,params = self.params,
                     num_boost_round=800)

        return self

    def predict(self, X:pd.DataFrame):
        test = X.copy()
        test["rank"] = -self.lgbst_rank.predict(test.drop(columns=self.not_features)[self.lgbst_rank.feature_name()])
        test["prob"] = test[["race_id","rank"]].groupby("race_id")["rank"].apply(lambda x: np.exp(x)/sum(np.exp(x)))
        probs = self.lgbst.predict(test.drop(columns=self.not_features)[self.lgbst.feature_name()])

        self.probs = probs

        return probs

    def make_bets(self,X:pd.DataFrame,kelly:float = 0.04, prob_min:float = 0.2, balance:int = 500):
        out = X[["date","horse_name","last_price",'race_id']].copy()
        try:
            out["model_prob"] = self.probs
        except AttributeError:
            out["model_prob"] = self.predict(X)
        out["kelly"] = ((out["model_prob"]*out["last_price"]) - 1)/(out["last_price"] - 1)
        out["bet"] = (out["model_prob"] > prob_min) & (out["kelly"] > kelly) & (out["kelly"] == out.groupby("race_id")["kelly"].transform("max"))
        out["bet_size"] = round(out["bet"]*out["kelly"]*balance,1)
        out.drop(columns=['race_id'])

        return out
