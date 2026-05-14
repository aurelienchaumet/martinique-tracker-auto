from dataclasses import dataclass, field
from typing import List, Optional
import yaml


@dataclass
class Choice:
    label: str
    next: str


@dataclass
class Node:
    id: str
    text: str
    choices: List[Choice]
    character: Optional[str] = None


@dataclass
class Character:
    id: str
    name: str


@dataclass
class Story:
    title: str
    version: int
    duration_min: int
    characters: List[Character]
    nodes: List[Node]


def load_story(path: str) -> Story:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    characters = [Character(**c) for c in data["characters"]]

    nodes = []
    for n in data["nodes"]:
        choices = [Choice(**c) for c in (n.get("choices") or [])]
        nodes.append(Node(
            id=n["id"],
            text=n["text"],
            choices=choices,
            character=n.get("character"),
        ))

    return Story(
        title=data["title"],
        version=data.get("version", 1),
        duration_min=data.get("duration_min", 10),
        characters=characters,
        nodes=nodes,
    )
