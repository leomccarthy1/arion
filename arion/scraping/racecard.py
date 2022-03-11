from .race import BaseRaceScraper
from re import sub

class RacecardScraper(BaseRaceScraper):
    def __init__(self, URL: str = None):
        super().__init__(URL)

    def get_distance(self):
        dist = self.extract_text(
            self.soup.find("strong", {"data-test-selector": "RC-header__raceDistanceRound"})
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
    
    def get_rating_band(self):
        bands_age = self.extract_text(
            self.soup.find_all(
                "span", {"data-test-selector": "RC-header__rpAges"}
            )
        )

        bands = bands_age[0].split()

        band_rating = ""

        if len(bands) > 1:
            for x in bands:
                if "-" in x:
                    band_rating = x.strip()
        else:
            if "-" in bands:
                band_rating = bands.strip()
        
        return band_rating



    def scrape_race(self):
        #Race info
        self.race_info["datetime"] = self.soup.find_all("section")[0].get(
            "data-card-race-date-time"
        )
        self.race_info["course"] = self.soup.find_all("section")[0].get(
            "data-card-coursename"
        )
        self.race_info["distance_f"] = self.get_distance()

        self.race_info["going"] = self.extract_text(
            self.soup.find_all("div", {"data-test-selector": "RC-ticker__going"})
        )[0].replace("Going: ", "")

        self.race_info["rating_band"] = self.get_rating_band()

        self.race_info["class"] = self.clean_numeric(
            self.extract_text(
                self.soup.find("span", {"data-test-selector": "RC-header__raceClass"})
            )
        )[0]

       #Runner info
        self.runner_info["horse_num"] = self.extract_text(
            self.soup.find_all("span", {"data-test-selector": "RC-cardPage-runnerNumber-no"})
        )

        self.runner_info["horse_name"] = self.extract_text(
            self.soup.find_all("a", {"data-test-selector": "RC-cardPage-runnerName"})
        )

        self.race_info["runners"] = len([r for r in self.runner_info["horse_num"] if r not in ['NR','Nr']])

        self.runner_info["jockey"] = self.extract_text(
            self.soup.find_all("a", {"data-test-selector": "RC-cardPage-runnerJockey-name"})
        )
        self.runner_info["trainer"] = self.extract_text(
            self.soup.find_all("a", {"data-test-selector": "RC-cardPage-runnerTrainer-name"}),
        )

        ran = len(self.runner_info['horse_name'])

        self.runner_info["price"] = ["0"] * ran


        self.runner_info["age"] = self.extract_text(
            self.soup.find_all("span", {"data-test-selector": "RC-cardPage-runnerAge"})
        )
        self.runner_info["draw"] = self.extract_text(
            self.soup.find_all("span", {"data-test-selector": "RC-cardPage-runnerNumber-draw"})
        )
        self.runner_info["rpr"] = self.clean_numeric(
            self.extract_text(self.soup.find_all("span",{"data-test-selector" :"RC-cardPage-runnerRpr"}))
        )
        self.runner_info["ts"] = self.clean_numeric(
            self.extract_text(self.soup.find_all("span",{"data-test-selector" : "RC-cardPage-runnerTs"}))
        )

        self.runner_info["or"] = self.clean_numeric(
            self.extract_text(self.soup.find_all("span",{"data-test-selector":"RC-cardPage-runnerOr"}))
        )

        self.runner_info["finish_pos"]= [""] * ran
        self.runner_info["ovr_btn"] = [""]* ran
        self.runner_info["prize"] = [""]* ran
        self.runner_info["comment"] = [""] * ran

        self.csv_data = self.create_csv_data()

        return self