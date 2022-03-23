#!/usr/bin/env bash

python pipeline/make_racecard.py --scrape_card=True --update_results=True &&
python main.py
