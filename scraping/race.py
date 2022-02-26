from typing import Callable, List

import requests
from bs4 import BeautifulSoup


class BaseRaceScraper:
    def __init__(self, url: str = None):
        self.url = url
        self.race_info = {}
        self.runner_info = {}

        self.page = requests.get(url)
        self.soup = BeautifulSoup(self.page.content, "html.parser")
        self.race_info['race_id'] = self.url.split('/')[7]
        self.race_info['course_id'] = self.url.split('/')[4]

    def clean_strings(self, string: str) -> str:

        return (
            string.strip()
            .replace(",", " ")
            .replace("'", "")
            .replace('"', "")
            .replace(")", "")
            .replace("(", "")
            .title()
            .replace(".", "")
            .replace("\x80", "")
            .replace("\\x80", "").replace("\xa0"," ")
        )

    def extract_text(
        self, html: List, skip: bool = False, dtype: Callable = str
    ) -> list:
        if html is None:
            return ['']
        elif skip:
            return [dtype(self.clean_strings(i.get_text())) for i in html][::2]
        else:
            return [dtype(self.clean_strings(i.get_text())) for i in html]

    def create_csv_data(self):
        csv_race_info = ''
        fields = [*self.race_info] +  [*self.runner_info]
        
        for field in fields:
            if field in self.race_info:
                csv_race_info += f'{self.race_info[field]},'
            
        runner_info = []
        
        for field in fields:
            if field in self.runner_info:
                runner_info.append(self.runner_info[field])
        
        csv = []
        
        for row in zip(*runner_info):
            csv.append(csv_race_info + ','.join(str(x) for x in row))
        
        return csv
