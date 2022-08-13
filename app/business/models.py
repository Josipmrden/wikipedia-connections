from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParagraphLink:
    text: str
    link: str
    context: str


@dataclass
class PersonDetails:
    name: str
    url: str
    birth_date: str
    death_date: Optional[str]

@dataclass
class PersonConnection:
    connection_person: PersonDetails
    context: str