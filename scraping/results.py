from race import BaseRaceScraper
import json
import os

URLS = [
    "https://www.racingpost.com/results/1353/newcastle-aw/2022-02-21/803348",
    "https://www.racingpost.com/results/393/lingfield-aw/2022-02-19/803339",
]

class VoidRaceError(Exception):
    pass


class ResultScraper(BaseRaceScraper):
    def __init__(self, URL: str = None):
        super().__init__(URL)

        # Get info for race condtions

        self.race_info["datetime"] = self.soup.find_all("main")[0].get(
            "data-analytics-race-date-time"
        )
        self.race_info["course"] = self.soup.find_all("main")[0].get(
            "data-analytics-coursename"
        )
        self.race_info["distance_f"] = self.get_distance()
        self.race_info["runners"] = self.get_num_runners()
        self.race_info["going"] = self.extract_text(
            self.soup.find_all("span", {"class": "rp-raceTimeCourseName_condition"})
        )[0]

        # Get info for all runners
        self.runner_info["horse_name"] = self.extract_text(
            self.soup.find_all("a", {"data-test-selector": "link-horseName"})
        )
        self.runner_info["jockey"] = self.extract_text(
            self.soup.find_all("a", {"data-test-selector": "link-jockeyName"}),
            skip=True,
        )
        self.runner_info["trainer"] = self.extract_text(
            self.soup.find_all("a", {"data-test-selector": "link-trainerName"}),
            skip=True,
        )
        self.runner_info["age"] = self.extract_text(
            self.soup.find_all("td", {"data-test-selector": "horse-age"})
        )
        self.runner_info["draw"] = self.extract_text(
            self.soup.find_all("sup", {"class": "rp-horseTable__pos__draw"})
        )
        self.runner_info["rpr"] = self.extract_text(
            self.soup.find_all("td", {"data-ending": "RPR"})
        )
        self.runner_info["ts"] = self.extract_text(
            self.soup.find_all("td", {"data-ending": "TS"})
        )
        self.runner_info["or"] = self.extract_text(
            self.soup.find_all("td", {"data-ending": "OR"})
        )
        self.runner_info["finish_pos"] = self.get_positions()
        self.runner_info["ovr_btn"] = self.get_lengths()
        self.runner_info["prize"] = self.get_prize()

        self.csv_data = self.create_csv_data()

    def get_num_runners(self):
        ran = self.extract_text(
            self.soup.find_all(
                "span", {"class": "rp-raceInfo__value rp-raceInfo__value_black"}
            )
        )[0]

        if ran is not None:
            return ran.replace("Ran", "").strip()

        return None

    def get_lengths(self):
        lens = []
        t = (
            self.soup.select(
                'script:-soup-contains("window.horseData")', type="application/ld+json"
            )[0]
            .text.split("=")[1]
            .replace(";", "")
        )
        t = json.loads(t)
        for i in t["items"]:
            lens.append(i["accumLengthNative"])
        lens[0] = 0

        return lens

    def get_positions(self):
        positions = self.extract_text(
            self.soup.find_all("span", {"data-test-selector": "text-horsePosition"})
        )

        try:        
            if positions[0] == 'VOI':
                raise VoidRaceError
        except:
            print(f"Voide race {self.url}")

        positions = [i[:2] for i in positions]

        return positions

    def get_prize(self):
        prizes = self.soup.find_all("div", {"data-test-selector": "text-prizeMoney"})
        prize = [p.get_text().split() for p in prizes][0][1::2]
        prize = [p.strip().replace(",", "").replace("£", "") for p in prize]
        pos = self.runner_info["finish_pos"]

        try:
            [prize.append("0") for i in range(len(pos) - len(prize))]
        except IndexError:
            prize = ["" for i in range(len(pos))]

        return prize

    def get_distance(self):
        dist = self.extract_text(
            self.soup.find_all("span", {"data-test-selector": "block-distanceInd"})
        )
        dist = "".join(
            [
                d.strip().replace("¼", ".25").replace("½", ".5").replace("¾", ".75")
                for d in dist
            ]
        )

        if "M" in dist:
            if len(dist) > 2:
                dist = int(dist.split("M")[0]) * 8 + float(
                    dist.split("M")[1].strip("F")
                )
            else:
                dist = int(dist.split("M")[0]) * 8
        else:
            dist = dist.strip("F")

        return dist


if not os.path.exists("scraping/data/"):
    os.makedirs("scraping/data/")

file_path = f"scraping/data/1.csv"


with open(file_path, "w", encoding="utf-8") as csv:
    first = True
    for URL in URLS:
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