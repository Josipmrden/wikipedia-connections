from abc import ABC

from app.business.models import ParagraphLink, PersonConnection, PersonDetails
from app.database.models import WikiPerson, WikiPersonLink
from app.database.repository import Repository

from tqdm import tqdm


class PersonLinkListener(ABC):
    def found_person_connection(
        self, person: PersonDetails, connection: PersonConnection
    ) -> None:
        pass


class ParagraphLinkListener(ABC):
    def found_paragraph_links(self, link: str, count: int) -> None:
        pass

    def processed_paragraph_link(self) -> None:
        pass


class DBInsertListener(PersonLinkListener):
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    def found_person_connection(
        self, person: PersonDetails, connection: PersonConnection
    ) -> None:
        wiki_person = WikiPerson(
            person.name, person.url, person.birth_date, person.death_date
        )
        connection_person = WikiPerson(
            connection.connection_person.name,
            connection.connection_person.url,
            connection.connection_person.birth_date,
            connection.connection_person.death_date,
        )

        link_between_persons = WikiPersonLink(
            wiki_person, connection_person, connection.context
        )

        self._repository.save_person(wiki_person)
        self._repository.save_person(connection_person)
        self._repository.link_persons(link_between_persons)


class ProgressParagraphLinkListener(PersonLinkListener):
    def found_paragraph_links(self, link: str, count: int) -> None:
        self._progress = tqdm(range(count))
        print(f"Found {count} links on url {link}")

    def processed_paragraph_link(self) -> None:
        self._progress.update(1)
