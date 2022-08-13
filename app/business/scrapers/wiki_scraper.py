import requests
from typing import Iterable, List
from bs4 import BeautifulSoup
from app.business.exceptions import PersonNotFoundException

from app.business.listeners import ParagraphLinkListener, PersonLinkListener
from app.business.models import ParagraphLink, PersonConnection, PersonDetails
from app.business.scrapers.common import AbstractWikiScraper
from app.business.scrapers.paragraph_scraper import ParagraphLinkScraper
from app.utils.utils import clean_text


class WikiScraper(AbstractWikiScraper):
    PARAGRAPH_TAG = "p"
    WIKIPEDIA_PAGE = "https://en.wikipedia.org"

    def __init__(self) -> None:
        self._connection_listeners: List[PersonLinkListener] = []
        self._paragraph_link_listeners: List[ParagraphLinkListener] = []

    def run(self, link: str) -> None:
        person: PersonDetails = self._fetch_person_details(link)

        if person is None:
            raise PersonNotFoundException(
                "The person you were looking for could not be found!"
            )

        self._scrape_person_connections(person, link)

    def notify_on_found_person_connection(
        self, person: PersonDetails, connection: PersonConnection
    ) -> None:
        for l in self._connection_listeners:
            l.found_person_connection(person, connection)

    def notify_on_found_paragraph_links(self, link: str, count) -> None:
        for l in self._paragraph_link_listeners:
            l.found_paragraph_links(link, count)

    def notify_on_processed_paragraph_link(self) -> None:
        for l in self._paragraph_link_listeners:
            l.processed_paragraph_link()

    def add_connection_listener(self, listener: PersonLinkListener) -> None:
        self._connection_listeners.append(listener)

    def remove_connection_listener(self, listener: PersonLinkListener) -> None:
        self._connection_listeners.remove(listener)

    def add_paragraph_link_listener(self, listener: ParagraphLinkListener) -> None:
        self._paragraph_link_listeners.append(listener)

    def remove_paragraph_link_listener(self, listener: ParagraphLinkListener) -> None:
        self._paragraph_link_listeners.remove(listener)

    def _fetch_person_details(self, link: str):
        page = requests.get(link)
        bs = BeautifulSoup(page.content, "html.parser")

        wiki_content = bs.find(id="mw-content-text")
        if wiki_content is None:
            return None

        wiki_content_children = list(wiki_content.children)
        if not len(wiki_content_children):
            return None

        wiki_content_text = wiki_content_children[0]
        person_info_table = wiki_content_text.find(class_="infobox vcard")

        if person_info_table is None:
            return None

        table_children = list(person_info_table.children)
        if not len(table_children):
            return None

        person_name = table_children[0].text

        date_of_birth_filter = list(
            filter(lambda x: x.text == "Born", person_info_table.find_all("th"))
        )
        if not len(date_of_birth_filter):
            return None

        date_of_birth_context = date_of_birth_filter[0]
        date_of_birth = clean_text(date_of_birth_context.next_sibling.text)

        date_of_death = None
        try:
            date_of_death_context = list(
                filter(lambda x: x.text == "Died", person_info_table.find_all("th"))
            )[0]
            date_of_death = clean_text(date_of_death_context.next_sibling.text)
        except Exception as e:
            pass

        return PersonDetails(person_name, link, date_of_birth, date_of_death)

    def _scrape_person_connections(self, person: PersonDetails, link: str) -> None:
        paragraphs: List[ParagraphLink] = self._fetch_paragraph_links(link)
        self.notify_on_found_paragraph_links(link, len(paragraphs))

        for connection in self._filter_connections(paragraphs):
            self.notify_on_found_person_connection(person, connection)

    def _fetch_paragraph_links(self, link: str) -> List[ParagraphLink]:
        scraper = ParagraphLinkScraper()
        scraper.run(link)

        return scraper.links

    def _filter_connections(
        self, paragraph_links: List[ParagraphLink]
    ) -> Iterable[PersonConnection]:
        for paragraph_link in paragraph_links:
            person_details = self._fetch_person_details(paragraph_link.link)

            self.notify_on_processed_paragraph_link()

            if person_details:
                connection = PersonConnection(person_details, paragraph_link.context)
                yield connection
