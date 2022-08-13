from abc import ABC

from app.business.models import PersonConnection, PersonDetails
from app.database.models import WikiPerson, WikiPersonLink
from app.database.repository import Repository


class PersonLinkListener(ABC):
    def found_person_link(
        self, person: PersonDetails, connection: PersonConnection
    ) -> None:
        pass


class DBInsertListener(PersonLinkListener):
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    def found_person_link(
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
