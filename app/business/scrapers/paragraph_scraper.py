import requests
import itertools
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from app.business.models import ParagraphLink
from app.business.scrapers.common import AbstractWikiScraper
from app.utils.utils import find_begin, find_end, form_sentence


class ParagraphLinkScraper(AbstractWikiScraper):
    REMOVE_TAGS = ["sup"]
    LINK_TAG = "a"
    PARAGRAPH_TAG = "p"
    WIKIPEDIA_PAGE = "https://en.wikipedia.org"

    @property
    def links(self) -> List[ParagraphLink]:
        return self._links

    def run(self, link: str) -> None:
        links = self._fetch_paragraph_links(link)
        self._links = links

    def _fetch_paragraph_links(self, link: str) -> List[ParagraphLink]:
        page = requests.get(link)
        bs = BeautifulSoup(page.content, "html.parser")

        text_content = list(bs.find(id="mw-content-text").children)[0]
        paragraph_text_content = list(
            filter(
                lambda x: x.name == ParagraphLinkScraper.PARAGRAPH_TAG,
                text_content.children,
            )
        )

        links_with_content = list(
            itertools.chain.from_iterable(
                map(self._process_paragraph_content, paragraph_text_content)
            )
        )

        return links_with_content

    def _process_paragraph_content(self, paragraph) -> List[ParagraphLink]:
        if not any(
            [x.name == ParagraphLinkScraper.LINK_TAG for x in paragraph.children]
        ):
            return []

        processed_children = list(
            filter(
                lambda x: isinstance(x, str)
                or x.name not in ParagraphLinkScraper.REMOVE_TAGS,
                paragraph.children,
            )
        )

        cleaned_children = list(
            map(
                lambda x: x
                if isinstance(x, str) or x.name == ParagraphLinkScraper.LINK_TAG
                else x.text,
                processed_children,
            )
        )

        paragraph_links = []
        for i, child in enumerate(cleaned_children):
            if (
                not isinstance(child, str)
                and child.name == ParagraphLinkScraper.LINK_TAG
            ):
                paragraph_link = self._create_paragraph_link(child, cleaned_children, i)
                paragraph_links.append(paragraph_link)

        return paragraph_links

    def _create_paragraph_link(self, link, context, order: int) -> ParagraphLink:
        text = link.attrs["title"]
        link_pointer = urljoin(ParagraphLinkScraper.WIKIPEDIA_PAGE, link.attrs["href"])
        context = self._extract_context(context, order)

        context = context if context.isprintable() else rf"{context}"
        paragraph_link = ParagraphLink(text, link_pointer, context)

        return paragraph_link

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
