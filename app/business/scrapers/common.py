from abc import ABC

class AbstractWikiScraper(ABC):
    def run(self, link: str) -> None:
        pass