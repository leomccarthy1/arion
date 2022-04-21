#!/usr/bin/env bash
python -m pipeline.make_racecard --scrape_card=True --update_results=True &&
python main.py
