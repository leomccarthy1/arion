# arion

4 easy steps to make money betting on horses. Find it all here :grin: :rocket:

1. Scrape historical horse racing data. 

2. Build features.

3. Train models.

4. Automatically place bets on the exchange using the kelly criterion, were a higher probability of winning is predicted than the market suggets



Simulated profit on last years flat horse racing data (held out from training and tunning).Bets are placed using the kelly criterion relative to a static starting bank of £1000. Different minimum predicted winning probibilities and minmum kelly value thresholds are shown. 

Best ROI with 5% BF commision accounted for is 15% from 3690 bets which is a 56x return on initial balance. 

![Simulated](notebooks/simulation.png?raw=true "Title")

## Data

- Last 12 years of flat horse raicing data scraped from racing websites.
- Last 7 years worth of Betfair exchange price data. 

## Features

Aprprox 400ish features extracted from raw results data.

Some examples are:

- Exponentially weighted moving avg of Horse, Trainer and Jockey prize money
- Horses SR on todays going conditions
- Trainer places at track 
- The avergace percentage of opponents beaten per race over a horse lifetime
- Ratings i.e racing post, official rating, speed rating etc
- Many more......

Also included as a predictor is the current exchange market price. It is generally agreed that as the race approaches off time the exchange market becomes more eficcient (and more liquid). That means close to the off time the prices offer a very good indication of a horses chances, it also means there are less likely to be any prices that offer a considerable amount of *value*. I've found that placing bets around 2-3 hours before the race hits a sweet spot of enough market liquidity and a market with enough prices that don't represent true chances of winning and thus offer a money making opportunity.

## Models

Eventually settled on a couple of stackled LightGBM models.

The first uses a LambdaRank objective function, the output of which is then pushed through a softmax function on a race by race basis.

The second uses binary logloss  objective. 


## Excecution 
A high level overview of the bet execution process is as follows

- Daily racecards (race data) scraped
- Features engeneiered 
- Stream live market data using [flumine](https://github.com/betcode-org/flumine)
- Predict win probabilities using trained models, extracted features and live betfair prices
- Place bets based on [kelly citerion](https://en.wikipedia.org/wiki/Kelly_criterion) in sitations were the predicted probiility is grrater than the current odds suggest
- Track bets placed and cleared orders

note: a minumum predicted probibility of 0.2 and kelly-optimal stake size of 0.04 are used as extra conditions to be met before bet placement. 
