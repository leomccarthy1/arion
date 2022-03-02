from race import BaseRaceScraper

class ResultScraper(BaseRaceScraper):
    def __init__(self, URL: str = None):
        super().__init__(URL)