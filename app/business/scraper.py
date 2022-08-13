import multiprocessing as mp
import requests
import itertools
from abc import ABC
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.business.listeners import PersonLinkListener
from app.business.models import ParagraphLink, PersonConnection, PersonDetails
from app.utils.utils import clean_text, find_begin, find_end, form_sentence


class AbstractWikiScraper(ABC):
    def run(self, link: str) -> None:
        pass


class WikiScraper(AbstractWikiScraper):
    REMOVE_TAGS = ["sup"]
    CLEAN_TAGS = ["b"]
    LINK_TAG = "a"
    PARAGRAPH_TAG = "p"
    WIKIPEDIA_PAGE = "https://en.wikipedia.org"

    def __init__(self) -> None:
        self.listeners: List[PersonLinkListener] = []

    def run(self, link: str) -> None:
        person: PersonDetails = self.scrape_person_details(link)
        paragraphs: List[ParagraphLink] = self.scrape_paragraph_links(person.url)
        connections: List[PersonConnection] = self.filter_connections(paragraphs)

        for connection in connections:
            self.notify_listeners(person, connection)

    def scrape_person_details(self, link: str):
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

    def scrape_paragraph_links(self, link: str) -> List[ParagraphLink]:
        page = requests.get(link)
        bs = BeautifulSoup(page.content, "html.parser")

        text_content = list(bs.find(id="mw-content-text").children)[0]
        paragraph_text_content = list(
            filter(lambda x: x.name == WikiScraper.PARAGRAPH_TAG, text_content.children)
        )

        links_with_content = list(
            itertools.chain.from_iterable(
                map(self._process_paragraph_content, paragraph_text_content)
            )
        )

        return links_with_content

    def filter_connections(
        self, paragraph_links: List[ParagraphLink]
    ) -> List[PersonDetails]:
        connections: List[PersonConnection] = []

        for paragraph_link in paragraph_links:
            person_details = self.scrape_person_details(paragraph_link.link)
            if person_details:
                connections.append(
                    PersonConnection(person_details, paragraph_link.context)
                )
                break

        return connections

    def notify_listeners(
        self, person: PersonDetails, connection: PersonConnection
    ) -> None:
        for l in self.listeners:
            l.found_person_link(person, connection)

    def add_listener(self, listener: PersonLinkListener) -> None:
        self.listeners.append(listener)

    def remove_listener(self, listener: PersonLinkListener) -> None:
        self.listeners.remove(listener)

    def _process_paragraph_content(self, paragraph) -> List[ParagraphLink]:
        if not any([x.name == WikiScraper.LINK_TAG for x in paragraph.children]):
            return []

        processed_children = list(
            filter(
                lambda x: isinstance(x, str) or x.name not in WikiScraper.REMOVE_TAGS,
                paragraph.children,
            )
        )

        cleaned_children = list(
            map(
                lambda x: x
                if isinstance(x, str) or x.name == WikiScraper.LINK_TAG
                else x.text,
                processed_children,
            )
        )

        paragraph_links = []
        for i, child in enumerate(cleaned_children):
            if not isinstance(child, str) and child.name == WikiScraper.LINK_TAG:
                paragraph_links.append(
                    self._create_paragraph_link(child, cleaned_children, i)
                )

        return paragraph_links

    def _create_paragraph_link(self, link, context, order: int) -> ParagraphLink:
        text = link.attrs["title"]
        link_pointer = urljoin(WikiScraper.WIKIPEDIA_PAGE, link.attrs["href"])
        context = self._extract_context(context, order)

        return ParagraphLink(text, link_pointer, context)

    def _extract_context(self, context, order: int) -> str:
        plain_text = list(map(lambda x: x if isinstance(x, str) else x.text, context))

        beginning_of_current = find_begin(context, order)
        end_of_current = find_end(context, order)

        current_sentence = form_sentence(
            plain_text, beginning_of_current, end_of_current
        )

        beginning_of_prev = find_begin(context, beginning_of_current)
        end_of_prev = beginning_of_current

        previous_sentence = (
            form_sentence(plain_text, beginning_of_prev, end_of_prev)
            if beginning_of_prev != beginning_of_current
            else ""
        )

        beginning_of_next = end_of_current
        end_of_next = find_end(context, end_of_current)

        next_sentence = (
            form_sentence(plain_text, beginning_of_next, end_of_next)
            if end_of_next != end_of_current
            else ""
        )

        return "".join([previous_sentence, current_sentence, next_sentence])
