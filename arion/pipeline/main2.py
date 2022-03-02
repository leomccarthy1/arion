from mimetypes import init
from arion.scraping.results import ResultScraper

class tr(ResultScraper):
    def __init__(self, URL: str = None):
        super().__init__(URL)