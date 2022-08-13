from abc import ABC
from typing import Optional
from gqlalchemy import Memgraph, Node, Relationship, Field

from app.database.models import WikiPerson, WikiPersonLink


class Repository(ABC):
    def save_person(wiki_person: WikiPerson):
        pass

    def link_persons(wiki_person_link: WikiPersonLink):
        pass


memgraph = Memgraph()


class MemgraphWikiPerson(Node):
    name: str = Field(index=True, exist=True, unique=True, db=memgraph)
    url: Optional[str] = Field(index=True, exist=True, unique=True, db=memgraph)
    birth_date: Optional[str] = Field(index=True, exist=True, unique=True, db=memgraph)
    death_date: Optional[str] = Field(index=True, exist=True, unique=True, db=memgraph)


class HasConnectionTo(Relationship, type="HAS_CONNECTION_TO"):
    context: str = Field()


class MemgraphRepository(Repository):
    def __init__(self) -> None:
        self._memgraph = memgraph

    def save_person(self, wiki_person: WikiPerson):
        MemgraphWikiPerson(
            name=wiki_person.name,
            url=wiki_person.url,
            birth_date=wiki_person.birth_date,
            death_date=wiki_person.death_date,
        ).save(self._memgraph)

    def link_persons(self, wiki_person_link: WikiPersonLink):
        first_person = wiki_person_link.from_person
        second_person = wiki_person_link.to_person

        first_ogm_person = MemgraphWikiPerson(name=first_person.name).load(
            self._memgraph
        )
        second_ogm_person = MemgraphWikiPerson(name=second_person.name).load(
            self._memgraph
        )

        HasConnectionTo(
            _start_node_id=first_ogm_person._id,
            _end_node_id=second_ogm_person._id,
            context=wiki_person_link.context,
        ).save(memgraph)
