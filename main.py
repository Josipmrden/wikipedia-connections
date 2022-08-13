from app.business.listeners import DBInsertListener, ProgressPersonLinkListener
from app.business.scrapers.wiki_scraper import WikiScraper
from app.database.repository import MemgraphRepository

dummy_url: str = "https://en.wikipedia.org/wiki/Michael_Jordan"


def main() -> None:
    wiki_scraper = WikiScraper()

    link = dummy_url

    wiki_scraper.add_listener(DBInsertListener(MemgraphRepository()))
    wiki_scraper.add_listener(ProgressPersonLinkListener())

    wiki_scraper.run(link)


if __name__ == "__main__":
    main()
