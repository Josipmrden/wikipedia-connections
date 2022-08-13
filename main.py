from app.business.listeners import DBInsertListener, ProgressParagraphLinkListener
from app.business.scrapers.wiki_scraper import WikiScraper
from app.database.repository import MemgraphRepository

dummy_url: str = "https://en.wikipedia.org/wiki/Michael_Jordan"


def main() -> None:
    wiki_scraper = WikiScraper()

    link = dummy_url

    wiki_scraper.add_connection_listener(DBInsertListener(MemgraphRepository()))
    wiki_scraper.add_paragraph_link_listener(ProgressParagraphLinkListener())

    wiki_scraper.run(link)


if __name__ == "__main__":
    main()
