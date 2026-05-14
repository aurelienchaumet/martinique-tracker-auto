import pytest
from src.story_schema import Choice, Node, Character, Story, load_story

FIXTURE = "tests/fixtures/valid_story.yaml"

def test_load_story_returns_story_instance():
    story = load_story(FIXTURE)
    assert isinstance(story, Story)

def test_load_story_title():
    story = load_story(FIXTURE)
    assert story.title == "Test Histoire"

def test_load_story_characters():
    story = load_story(FIXTURE)
    assert len(story.characters) == 2
    assert story.characters[0].id == "renard"
    assert story.characters[1].name == "Chouette"

def test_load_story_nodes():
    story = load_story(FIXTURE)
    assert len(story.nodes) == 6

def test_node_choices_parsed():
    story = load_story(FIXTURE)
    intro = next(n for n in story.nodes if n.id == "intro")
    assert len(intro.choices) == 2
    assert intro.choices[0].label == "Le Renard"
    assert intro.choices[0].next == "renard_depart"

def test_end_node_has_empty_choices():
    story = load_story(FIXTURE)
    fin = next(n for n in story.nodes if n.id == "renard_fin_a")
    assert fin.choices == []

def test_node_character_optional():
    story = load_story(FIXTURE)
    intro = next(n for n in story.nodes if n.id == "intro")
    assert intro.character is None

def test_node_character_set():
    story = load_story(FIXTURE)
    depart = next(n for n in story.nodes if n.id == "renard_depart")
    assert depart.character == "renard"
