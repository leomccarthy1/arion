import json
import os
from datetime import date, timedelta, datetime

import requests
from bs4 import BeautifulSoup
from fire import Fire
from tqdm import tqdm

from arion.scraping.results import ResultScraper
from arion.scraping.racecard import RacecardScraper

class VoidRaceError(Exception):
    pass


def courses(code="gb"):
    courses = json.loads(open("arion/scraping/_courses", "r").read())
    for id, course in courses[code].items():
        yield id, course


def get_dates(date_str):
    if "/" not in date_str:
        return parse_years(date_str)
    elif "-" in date_str:
        start_year, start_month, start_day = date_str.split("-")[0].split("/")
        end_year, end_month, end_day = date_str.split("-")[1].split("/")

        start_date = date(int(start_year), int(start_month), int(start_day))
        end_date = date(int(end_year), int(end_month), int(end_day))

        return [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]
    else:
        year, month, day = date_str.split("/")

        return [date(int(year), int(month), int(day))]


def parse_years(year_str):
    if "-" in year_str:
        try:
            return [
                str(x)
                for x in range(
                    int(year_str.split("-")[0]), int(year_str.split("-")[1]) + 1
                )
            ]
        except ValueError:
            return []
    else:
        return [year_str]


def get_race_urls(tracks, years, code):
    urls = set()
    courses = []

    course_url = "https://www.racingpost.com:443/profile/course/filter/results"
    result_url = "https://www.racingpost.com/results"

    for track in tracks:
        for year in years:
            courses.append((track, f"{course_url}/{track[0]}/{year}/{code}/all-races"))

    races = [
        [
            course[0],
            requests.get(course[1], headers={"User-Agent": "Mozilla/5.0"}).json(),
        ]
        for course in courses
    ]
    for race in races:
        results = race[1]["data"]["principleRaceResults"]
        if results:
            for result in results:
                url = f'{result_url}/{race[0][0]}/{race[0][1]}/{result["raceDatetime"][:10]}/{result["raceInstanceUid"]}'
                urls.add(url.replace(" ", "-").replace("'", ""))

    return sorted(list(urls))


def get_race_urls_date(dates, region):
    urls = set()

    days = [f"https://www.racingpost.com/results/{d}" for d in dates]
    docs = [requests.get(day, headers={"User-Agent": "Mozilla/5.0"}) for day in days]

    course_ids = {course[0] for course in courses(region)}

    for doc in docs:
        soup = BeautifulSoup(doc.content, "html.parser")
        race_links = soup.find_all(
            "a", {"data-test-selector": "link-listCourseNameLink"}
        )

        for race in race_links:
            if race["href"].split("/")[2] in course_ids:
                urls.add("https://www.racingpost.com" + race["href"])

    return sorted(list(urls))

def scrape_races(
    dates: str, folder: str = "data", type: str = "historic", code: str = "flat"
):
    dates = str(dates)
    file_path = f"{folder}/{dates.replace('/', '_')}.csv"
    if "/" in dates:
        dates = get_dates(dates)
        URLS = get_race_urls_date(dates, "gb")
    else:
        dates = get_dates(dates)
        tracks = courses("gb")
        URLS = get_race_urls(tracks=tracks, years=dates, code=code)

    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(file_path, "w", encoding="utf-8") as csv:
        first = True
        for URL in tqdm(URLS):
            try:
                race = ResultScraper(URL)
            except VoidRaceError:
                continue
            while first:
                fields = [*race.race_info] + [*race.runner_info]
                csv.write(",".join(fields) + "\n")
                first = False
            for row in race.csv_data:
                csv.write(row + "\n")



def get_urls_racecard(dates:str, region:str = 'gb'):
    cards_page = requests.get(f"https://www.racingpost.com/racecards/{dates}", headers={"User-Agent": "Mozilla/5.0"})

    soup = BeautifulSoup(cards_page.content, "html.parser")
    race_links = soup.find_all(
            "a", {"class": "RC-meetingItem__link js-navigate-url"}, href=True
        )

    course_ids = {course[0] for course in courses(region)}
    urls = set()

    for race in race_links:
        if race["href"].split("/")[2] in course_ids:
            urls.add("https://www.racingpost.com" + race["href"])

    return sorted(list(urls))
    


def scrape_racecard(day:str = 'today', folder:str = 'data/racecards/raw'):

    if day == 'today':
        dates = datetime.today().strftime("%Y-%m-%d")
    URLS = get_urls_racecard(dates, "gb")
    file_path = f"{folder}/{dates.replace('-','_')}.csv"

    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(file_path, "w", encoding="utf-8") as csv:
        first = True
        for URL in tqdm(URLS):
            try:
                card_scraper = RacecardScraper(URL)
                race  = card_scraper.scrape_race()
            except VoidRaceError:
                continue
            while first:
                fields = [*race.race_info] + [*race.runner_info]
                csv.write(",".join(fields) + "\n")
                first = False
            for row in race.csv_data:
                csv.write(row + "\n")