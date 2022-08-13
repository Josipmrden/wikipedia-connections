from dataclasses import dataclass
from typing import Optional


@dataclass
class WikiPerson:
    name: str
    url: str
    birth_date: str
    death_date: Optional[str]


@dataclass
class WikiPersonLink:
    from_person: WikiPerson
    to_person: WikiPerson
    context: str
