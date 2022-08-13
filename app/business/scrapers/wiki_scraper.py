import requests
from typing import List
from bs4 import BeautifulSoup
from app.business.exceptions import PersonNotFoundException

from app.business.listeners import PersonLinkListener
from app.business.models import ParagraphLink, PersonConnection, PersonDetails
from app.business.scrapers.common import AbstractWikiScraper
from app.business.scrapers.paragraph_scraper import ParagraphLinkScraper
from app.utils.utils import clean_text


class WikiScraper(AbstractWikiScraper):
    PARAGRAPH_TAG = "p"
    WIKIPEDIA_PAGE = "https://en.wikipedia.org"

    def __init__(self) -> None:
        self._listeners: List[PersonLinkListener] = []

    def run(self, link: str) -> None:
        person: PersonDetails = self._fetch_person_details(link)

        if person is None:
            raise PersonNotFoundException(
                "The person you were looking for could not be found!"
            )

        connections: List[PersonConnection] = self._fetch_connections(link)

        for connection in connections:
            self.notify_on_found_person_connection(person, connection)

    def notify_on_found_connection_group(self, link: str, count: int) -> None:
        for l in self._listeners:
            l.found_connection_group(link, count)

    def notify_on_found_person_connection(
        self, person: PersonDetails, connection: PersonConnection
    ) -> None:
        for l in self._listeners:
            l.found_person_connection(person, connection)

    def add_listener(self, listener: PersonLinkListener) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: PersonLinkListener) -> None:
        self._listeners.remove(listener)

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

    def _fetch_connections(self, link: str) -> List[PersonConnection]:
        paragraphs: List[ParagraphLink] = self._fetch_paragraph_links(link)
        self.notify_on_found_connection_group(link, len(paragraphs))
        
        connections: List[PersonConnection] = self._filter_connections(paragraphs)

        return connections

    def _fetch_paragraph_links(self, link: str) -> List[ParagraphLink]:
        scraper = ParagraphLinkScraper()
        scraper.run(link)

        return scraper.links

    def _filter_connections(
        self, paragraph_links: List[ParagraphLink]
    ) -> List[PersonConnection]:
        connections: List[PersonConnection] = []

        for paragraph_link in paragraph_links:
            person_details = self._fetch_person_details(paragraph_link.link)
            if person_details:
                connections.append(
                    PersonConnection(person_details, paragraph_link.context)
                )
                break

        return connections
