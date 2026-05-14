# Créateur d'histoires Lunii Flam — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deux scripts Python — un assistant CLI d'écriture et un générateur de pack — permettant de créer des histoires interactives personnalisées pour la boîte à histoires Lunii Flam.

**Architecture:** Un module partagé `src/story_schema.py` définit le modèle de données et la validation YAML. `create_story.py` guide l'auteur via un wizard CLI et génère un `story.yaml` avec textes narratifs. `generate_pack.py` valide le YAML, produit la liste audio et assemble le pack STUdio importable.

**Tech Stack:** Python 3.8+, PyYAML, pytest, zipfile (stdlib), uuid (stdlib), dataclasses (stdlib)

---

## Structure des fichiers

```
claude_martinique/
├── create_story.py           # CLI wizard d'écriture
├── generate_pack.py          # CLI générateur de pack STUdio
├── src/
│   ├── __init__.py
│   ├── story_schema.py       # Dataclasses + parsing YAML + validation
│   ├── story_templates.py    # Génération de textes placeholder
│   ├── audio_export.py       # Génération de audio_to_synthesize.txt
│   └── studio_format.py      # Construction du pack STUdio (story.json + ZIP)
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   └── valid_story.yaml  # Histoire minimale pour les tests
│   ├── test_story_schema.py
│   ├── test_story_templates.py
│   ├── test_audio_export.py
│   └── test_studio_format.py
├── stories/                  # Fichiers YAML des histoires
└── assets/                   # Fichiers audio .ogg
```

---

## Tâche 1 : Setup + recherche du format STUdio

**Fichiers :**
- Créer : `requirements.txt`
- Créer : `src/__init__.py`, `tests/__init__.py`, `tests/fixtures/`

- [ ] **Étape 1 : Installer les dépendances**

```bash
pip install pyyaml pytest
```

Créer `requirements.txt` :
```
pyyaml>=6.0
pytest>=7.0
```

- [ ] **Étape 2 : Créer la structure de dossiers**

```bash
mkdir -p src tests/fixtures stories assets
touch src/__init__.py tests/__init__.py
```

- [ ] **Étape 3 : Exporter un pack STUdio existant pour analyser le format**

Dans STUdio (déjà installé) :
1. Ouvrir une histoire existante (ou en créer une très simple avec 2 nœuds)
2. Fichier → Exporter le pack → choisir un dossier
3. Dézipper le `.zip` exporté et examiner sa structure

Documenter dans un fichier `docs/studio_format_notes.md` :
- Noms et structure des fichiers dans le ZIP
- Contenu de `story.json` (ou équivalent) : copier un exemple
- Format des UUIDs des nœuds
- Champs de `stageNodes` et `actionNodes`
- Format audio requis (.ogg ou autre)

> Ce format est la référence pour implémenter `studio_format.py` en Tâche 7. Toute divergence avec le plan ci-dessous doit être corrigée à la Tâche 7.

- [ ] **Étape 4 : Commit**

```bash
git init
git add requirements.txt src/__init__.py tests/__init__.py
git commit -m "chore: setup projet créateur histoires Lunii Flam"
```

---

## Tâche 2 : Modèle de données (`src/story_schema.py`)

**Fichiers :**
- Créer : `src/story_schema.py`
- Créer : `tests/fixtures/valid_story.yaml`
- Créer : `tests/test_story_schema.py`

- [ ] **Étape 1 : Créer la fixture de test**

Créer `tests/fixtures/valid_story.yaml` :
```yaml
title: "Test Histoire"
version: 1
duration_min: 5

characters:
  - id: renard
    name: "Renard"
  - id: chouette
    name: "Chouette"

nodes:
  - id: intro
    text: "Bienvenue dans cette aventure. Qui veux-tu incarner ?"
    choices:
      - label: "Le Renard"
        next: renard_depart
      - label: "La Chouette"
        next: chouette_depart

  - id: renard_depart
    character: renard
    text: "Tu es Renard, malin et curieux. La forêt s'étend devant toi."
    choices:
      - label: "Aller à droite"
        next: renard_fin_a
      - label: "Aller à gauche"
        next: renard_fin_b

  - id: renard_fin_a
    character: renard
    text: "Tu trouves un abri douillet. Bravo !"
    choices: []

  - id: renard_fin_b
    character: renard
    text: "Tu découvres un trésor caché !"
    choices: []

  - id: chouette_depart
    character: chouette
    text: "Tu es Chouette, sage et observatrice. La nuit tombe."
    choices:
      - label: "Voler vers le nord"
        next: chouette_fin
      - label: "Rester sur place"
        next: chouette_fin

  - id: chouette_fin
    character: chouette
    text: "Tu guides tous les animaux à bon port. Quelle sagesse !"
    choices: []
```

- [ ] **Étape 2 : Écrire les tests**

Créer `tests/test_story_schema.py` :
```python
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
```

- [ ] **Étape 3 : Exécuter les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_story_schema.py -v
```
Résultat attendu : `ImportError` ou `ModuleNotFoundError`

- [ ] **Étape 4 : Implémenter `src/story_schema.py`**

```python
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
```

- [ ] **Étape 5 : Exécuter les tests**

```bash
pytest tests/test_story_schema.py -v
```
Résultat attendu : tous les tests PASS

- [ ] **Étape 6 : Commit**

```bash
git add src/story_schema.py tests/test_story_schema.py tests/fixtures/valid_story.yaml
git commit -m "feat: modèle de données Story + chargement YAML"
```

---

## Tâche 3 : Validation du YAML (`src/story_schema.py`)

**Fichiers :**
- Modifier : `src/story_schema.py` (ajouter `validate_story`)
- Modifier : `tests/test_story_schema.py`

- [ ] **Étape 1 : Écrire les tests de validation**

Ajouter dans `tests/test_story_schema.py` :
```python
from src.story_schema import validate_story, StoryValidationError

def test_validate_valid_story():
    story = load_story(FIXTURE)
    # ne lève pas d'exception
    validate_story(story)

def test_validate_duplicate_ids():
    story = load_story(FIXTURE)
    story.nodes.append(Node(id="intro", text="Doublon", choices=[]))
    with pytest.raises(StoryValidationError, match="ID dupliqué"):
        validate_story(story)

def test_validate_broken_link():
    story = load_story(FIXTURE)
    story.nodes[0].choices[0].next = "noeud_inexistant"
    with pytest.raises(StoryValidationError, match="lien cassé"):
        validate_story(story)

def test_validate_orphan_node():
    story = load_story(FIXTURE)
    from src.story_schema import Node
    story.nodes.append(Node(id="orphelin", text="Personne ne vient ici.", choices=[]))
    with pytest.raises(StoryValidationError, match="orphelin"):
        validate_story(story)

def test_validate_too_many_choices():
    story = load_story(FIXTURE)
    story.nodes[0].choices.append(Choice(label="Option C", next="renard_fin_a"))
    story.nodes[0].choices.append(Choice(label="Option D", next="renard_fin_a"))
    with pytest.raises(StoryValidationError, match="maximum 3 choix"):
        validate_story(story)

def test_validate_unknown_character():
    story = load_story(FIXTURE)
    story.nodes[1].character = "dragon_inconnu"
    with pytest.raises(StoryValidationError, match="personnage inconnu"):
        validate_story(story)
```

- [ ] **Étape 2 : Exécuter les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_story_schema.py -k "validate" -v
```
Résultat attendu : `ImportError` sur `validate_story`

- [ ] **Étape 3 : Implémenter `validate_story` dans `src/story_schema.py`**

Ajouter à la fin de `src/story_schema.py` :
```python
class StoryValidationError(Exception):
    pass


def validate_story(story: Story) -> None:
    node_ids = [n.id for n in story.nodes]
    character_ids = {c.id for c in story.characters}

    # IDs dupliqués
    seen = set()
    for nid in node_ids:
        if nid in seen:
            raise StoryValidationError(f"ID dupliqué : '{nid}'")
        seen.add(nid)

    node_id_set = set(node_ids)
    reachable = set()

    for node in story.nodes:
        # Trop de choix
        if len(node.choices) > 3:
            raise StoryValidationError(
                f"Nœud '{node.id}' : maximum 3 choix (actuel : {len(node.choices)})"
            )
        # Personnage inconnu
        if node.character and node.character not in character_ids:
            raise StoryValidationError(
                f"Nœud '{node.id}' : personnage inconnu '{node.character}'"
            )
        # Liens cassés
        for choice in node.choices:
            if choice.next not in node_id_set:
                raise StoryValidationError(
                    f"Nœud '{node.id}' : lien cassé vers '{choice.next}'"
                )
            reachable.add(choice.next)

    # Nœuds orphelins (non accessibles depuis aucun choix, sauf intro = premier nœud)
    first_id = story.nodes[0].id
    for node in story.nodes[1:]:
        if node.id not in reachable:
            raise StoryValidationError(
                f"Nœud orphelin : '{node.id}' n'est référencé par aucun choix"
            )
```

- [ ] **Étape 4 : Exécuter tous les tests**

```bash
pytest tests/test_story_schema.py -v
```
Résultat attendu : tous les tests PASS

- [ ] **Étape 5 : Commit**

```bash
git add src/story_schema.py tests/test_story_schema.py
git commit -m "feat: validation YAML (IDs dupliqués, liens cassés, orphelins, limites)"
```

---

## Tâche 4 : Génération de textes narratifs (`src/story_templates.py`)

**Fichiers :**
- Créer : `src/story_templates.py`
- Créer : `tests/test_story_templates.py`

- [ ] **Étape 1 : Écrire les tests**

Créer `tests/test_story_templates.py` :
```python
from src.story_templates import generate_story_yaml, WizardParams

def make_params(**kwargs):
    defaults = dict(
        title="Test",
        universe="animaux",
        characters=["Renard", "Chouette"],
        setting="une forêt dense",
        danger="une tempête",
        objective="trouver un abri",
        num_choices=3,
    )
    defaults.update(kwargs)
    return WizardParams(**defaults)

def test_generate_returns_dict():
    params = make_params()
    result = generate_story_yaml(params)
    assert isinstance(result, dict)

def test_generate_has_required_keys():
    params = make_params()
    result = generate_story_yaml(params)
    assert "title" in result
    assert "characters" in result
    assert "nodes" in result

def test_generate_title():
    params = make_params(title="Ma Belle Histoire")
    result = generate_story_yaml(params)
    assert result["title"] == "Ma Belle Histoire"

def test_generate_characters_count():
    params = make_params(characters=["Aigle", "Dauphin", "Loup"])
    result = generate_story_yaml(params)
    assert len(result["characters"]) == 3

def test_generate_intro_node_exists():
    params = make_params()
    result = generate_story_yaml(params)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "intro" in node_ids

def test_generate_intro_choices_match_characters():
    params = make_params(characters=["Renard", "Chouette"])
    result = generate_story_yaml(params)
    intro = next(n for n in result["nodes"] if n["id"] == "intro")
    assert len(intro["choices"]) == 2

def test_generate_all_links_valid():
    """Vérifie que le YAML généré passe la validation."""
    from src.story_schema import load_story, validate_story
    import yaml, tempfile, os
    params = make_params()
    data = generate_story_yaml(params)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml",
                                    delete=False, encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
        path = f.name
    try:
        story = load_story(path)
        validate_story(story)  # ne doit pas lever d'exception
    finally:
        os.unlink(path)

def test_generate_texts_contain_setting():
    params = make_params(setting="une grotte mystérieuse")
    result = generate_story_yaml(params)
    all_texts = " ".join(n["text"] for n in result["nodes"])
    assert "grotte mystérieuse" in all_texts

def test_generate_end_nodes_have_no_choices():
    params = make_params(num_choices=2)
    result = generate_story_yaml(params)
    end_nodes = [n for n in result["nodes"] if n["choices"] == []]
    assert len(end_nodes) >= 2
```

- [ ] **Étape 2 : Exécuter les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_story_templates.py -v
```
Résultat attendu : `ImportError`

- [ ] **Étape 3 : Implémenter `src/story_templates.py`**

```python
from dataclasses import dataclass
from typing import List
import re


UNIVERSE_VOCAB = {
    "animaux": {
        "monde": "Dans la forêt sauvage",
        "ambiance": "Les oiseaux se taisent soudainement.",
        "formule_magie": None,
    },
    "magie": {
        "monde": "Dans le royaume enchanté",
        "ambiance": "Des étincelles colorées dansent dans l'air.",
        "formule_magie": "Par les étoiles et la lune !",
    },
    "sorcières": {
        "monde": "Dans le village au bord du marais",
        "ambiance": "Une fumée violette s'élève d'un vieux chaudron.",
        "formule_magie": "Abracadabra, que la magie opère !",
    },
    "aventure": {
        "monde": "Au bout du monde connu",
        "ambiance": "Le vent souffle fort et le ciel s'assombrit.",
        "formule_magie": None,
    },
}


@dataclass
class WizardParams:
    title: str
    universe: str
    characters: List[str]
    setting: str
    danger: str
    objective: str
    num_choices: int


def _slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[àâä]", "a", name)
    name = re.sub(r"[éèêë]", "e", name)
    name = re.sub(r"[îï]", "i", name)
    name = re.sub(r"[ôö]", "o", name)
    name = re.sub(r"[ùûü]", "u", name)
    name = re.sub(r"[ç]", "c", name)
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def _generate_branch(
    char_slug: str, char_name: str, params: WizardParams, depth: int, path: str
) -> List[dict]:
    """Génère récursivement les nœuds d'une branche de personnage."""
    vocab = UNIVERSE_VOCAB.get(params.universe, UNIVERSE_VOCAB["aventure"])
    nodes = []

    if depth == 0:
        # Nœud de fin
        node_id = f"{char_slug}_fin_{path}"
        nodes.append({
            "id": node_id,
            "character": char_slug,
            "text": (
                f"Grâce à ton courage et ta persévérance, {char_name} atteint enfin son but : "
                f"{params.objective}. {vocab['ambiance']} "
                f"Tu as réussi cette aventure dans {params.setting} !"
            ),
            "choices": [],
        })
        return nodes

    # Nœud de choix
    choice_num = params.num_choices - depth + 1
    node_id = f"{char_slug}_choix{choice_num}_{path}"

    option_a_id = f"{char_slug}_choix{choice_num + 1}_{path}a" if depth > 1 else f"{char_slug}_fin_{path}a"
    option_b_id = f"{char_slug}_choix{choice_num + 1}_{path}b" if depth > 1 else f"{char_slug}_fin_{path}b"

    action_a = "foncer courageusement" if choice_num % 2 == 1 else "chercher une ruse"
    action_b = "demander de l'aide" if choice_num % 2 == 1 else "trouver un chemin détourné"

    nodes.append({
        "id": node_id,
        "character": char_slug,
        "text": (
            f"Moment crucial pour {char_name} ! {vocab['ambiance']} "
            f"Le danger approche : {params.danger}. "
            f"Deux options s'offrent à toi dans {params.setting}. "
            f"Que décides-tu ?"
        ),
        "choices": [
            {"label": action_a.capitalize(), "next": option_a_id},
            {"label": action_b.capitalize(), "next": option_b_id},
        ],
    })

    # Branches récursives
    nodes.extend(_generate_branch(char_slug, char_name, params, depth - 1, path + "a"))
    nodes.extend(_generate_branch(char_slug, char_name, params, depth - 1, path + "b"))

    return nodes


def generate_story_yaml(params: WizardParams) -> dict:
    vocab = UNIVERSE_VOCAB.get(params.universe, UNIVERSE_VOCAB["aventure"])

    characters = [
        {"id": _slugify(c), "name": c}
        for c in params.characters
    ]

    # Nœud intro
    intro_choices = [
        {"label": c["name"], "next": f"{c['id']}_depart"}
        for c in characters
    ]

    intro_node = {
        "id": "intro",
        "text": (
            f"{vocab['monde']}, une nouvelle aventure commence. "
            f"{params.danger} menace {params.setting}. "
            f"Un héros doit se lever pour {params.objective}. "
            f"{vocab['ambiance']} "
            f"Quel personnage veux-tu incarner ?"
        ),
        "choices": intro_choices,
    }

    nodes = [intro_node]

    for char in characters:
        char_slug = char["id"]
        char_name = char["name"]

        # Nœud de départ du personnage
        first_choice_id = (
            f"{char_slug}_choix1_a"
            if params.num_choices > 0
            else f"{char_slug}_fin_"
        )
        second_choice_id = (
            f"{char_slug}_choix1_b"
            if params.num_choices > 0
            else f"{char_slug}_fin_"
        )

        formule = f" {vocab['formule_magie']}" if vocab["formule_magie"] else ""

        depart_node = {
            "id": f"{char_slug}_depart",
            "character": char_slug,
            "text": (
                f"Te voilà dans la peau de {char_name} !{formule} "
                f"Tu te trouves dans {params.setting} et tu sens que {params.danger} approche. "
                f"Ton objectif : {params.objective}. "
                f"Il va falloir faire preuve de courage. Par où commences-tu ?"
            ),
            "choices": [
                {"label": "Explorer les environs", "next": first_choice_id},
                {"label": "Chercher des alliés", "next": second_choice_id},
            ],
        }
        nodes.append(depart_node)

        # Branches de choix
        branch_a = _generate_branch(char_slug, char_name, params, params.num_choices, "a")
        branch_b = _generate_branch(char_slug, char_name, params, params.num_choices, "b")
        nodes.extend(branch_a)
        nodes.extend(branch_b)

    # Estimation durée : ~30 secondes par nœud
    duration_min = max(5, len(nodes) * 30 // 60)

    return {
        "title": params.title,
        "version": 1,
        "duration_min": duration_min,
        "characters": characters,
        "nodes": nodes,
    }
```

- [ ] **Étape 4 : Exécuter les tests**

```bash
pytest tests/test_story_templates.py -v
```
Résultat attendu : tous les tests PASS

- [ ] **Étape 5 : Commit**

```bash
git add src/story_templates.py tests/test_story_templates.py
git commit -m "feat: génération de textes narratifs placeholder par univers"
```

---

## Tâche 5 : Assistant d'écriture CLI (`create_story.py`)

**Fichiers :**
- Créer : `create_story.py`

- [ ] **Étape 1 : Implémenter `create_story.py`**

```python
#!/usr/bin/env python3
"""Assistant CLI de création d'histoires pour Lunii Flam."""
import sys
import os
import yaml
from src.story_templates import WizardParams, generate_story_yaml

UNIVERSES = ["animaux", "magie", "sorcières", "aventure"]
UNIVERSE_LABELS = {
    "animaux": "Animaux & Nature",
    "magie": "Magie & Merveilles",
    "sorcières": "Sorcières & Potions",
    "aventure": "Aventure & Exploration",
}


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix} > ").strip()
    return val if val else default


def ask_int(prompt: str, min_val: int, max_val: int, default: int) -> int:
    while True:
        raw = ask(f"{prompt} ({min_val}-{max_val})", str(default))
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
        except ValueError:
            pass
        print(f"  ⚠ Entrez un nombre entre {min_val} et {max_val}.")


def ask_universe() -> str:
    print("\nUnivers disponibles :")
    for i, key in enumerate(UNIVERSES, 1):
        print(f"  {i}. {UNIVERSE_LABELS[key]}")
    while True:
        raw = ask("Choisis un univers (numéro)", "1")
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(UNIVERSES):
                return UNIVERSES[idx]
        except ValueError:
            pass
        print(f"  ⚠ Entrez un numéro entre 1 et {len(UNIVERSES)}.")


def ask_characters() -> list:
    count = ask_int("Combien de personnages jouables ?", 2, 4, 2)
    characters = []
    for i in range(1, count + 1):
        name = ask(f"  Nom du personnage {i}").strip()
        while not name:
            name = ask(f"  Nom du personnage {i} (obligatoire)").strip()
        characters.append(name)
    return characters


def main():
    print("\n🎙️  Créateur d'histoires Lunii Flam")
    print("=" * 40)

    title = ask("Titre de l'histoire").strip()
    while not title:
        title = ask("Titre (obligatoire)").strip()

    universe = ask_universe()
    characters = ask_characters()
    setting = ask("Lieu / décor de l'aventure", "une forêt mystérieuse")
    danger = ask("Danger ou obstacle principal", "une tempête qui approche")
    objective = ask("Objectif du héros", "trouver un refuge avant la nuit")
    num_choices = ask_int("Nombre de moments de choix dans l'histoire", 2, 5, 3)

    params = WizardParams(
        title=title,
        universe=universe,
        characters=characters,
        setting=setting,
        danger=danger,
        objective=objective,
        num_choices=num_choices,
    )

    print("\n⏳ Génération de l'histoire...")
    data = generate_story_yaml(params)

    # Nom de fichier
    slug = title.lower().replace(" ", "_")
    slug = "".join(c if c.isalnum() or c == "_" else "" for c in slug)
    os.makedirs("stories", exist_ok=True)
    output_path = f"stories/{slug}.yaml"

    # Éviter d'écraser un fichier existant
    counter = 1
    while os.path.exists(output_path):
        output_path = f"stories/{slug}_{counter}.yaml"
        counter += 1

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    node_count = len(data["nodes"])
    end_count = sum(1 for n in data["nodes"] if not n["choices"])

    print(f"\n✅ Histoire créée : {output_path}")
    print(f"   {node_count} nœuds au total, {end_count} fins différentes")
    print(f"   Durée estimée : ~{data['duration_min']} minutes")
    print(f"\n📝 Ouvre {output_path} pour affiner les textes.")
    print("   Lance ensuite : python generate_pack.py " + output_path)


if __name__ == "__main__":
    main()
```

- [ ] **Étape 2 : Tester manuellement le wizard**

```bash
python create_story.py
```

Répondre aux questions et vérifier que `stories/<titre>.yaml` est créé. Ouvrir le fichier et vérifier que les textes sont cohérents et que la structure est valide.

- [ ] **Étape 3 : Valider le YAML généré**

```python
# Test rapide en ligne de commande Python
from src.story_schema import load_story, validate_story
story = load_story("stories/<ton_fichier>.yaml")
validate_story(story)
print("Validation OK")
```

- [ ] **Étape 4 : Commit**

```bash
git add create_story.py
git commit -m "feat: assistant CLI de création d'histoires interactives"
```

---

## Tâche 6 : Exporteur de liste audio (`src/audio_export.py`)

**Fichiers :**
- Créer : `src/audio_export.py`
- Créer : `tests/test_audio_export.py`

- [ ] **Étape 1 : Écrire les tests**

Créer `tests/test_audio_export.py` :
```python
import os, tempfile
from src.story_schema import load_story
from src.audio_export import generate_audio_list

FIXTURE = "tests/fixtures/valid_story.yaml"

def test_generate_audio_list_creates_file():
    story = load_story(FIXTURE)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "audio_list.txt")
        generate_audio_list(story, out)
        assert os.path.exists(out)

def test_generate_audio_list_one_entry_per_node():
    story = load_story(FIXTURE)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "audio_list.txt")
        generate_audio_list(story, out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        entries = [b for b in content.split("\n\n") if b.strip()]
        assert len(entries) == len(story.nodes)

def test_generate_audio_list_contains_filename_header():
    story = load_story(FIXTURE)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "audio_list.txt")
        generate_audio_list(story, out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert "# Fichier : intro.ogg" in content

def test_generate_audio_list_contains_text():
    story = load_story(FIXTURE)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "audio_list.txt")
        generate_audio_list(story, out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        assert "Bienvenue dans cette aventure" in content
```

- [ ] **Étape 2 : Exécuter les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_audio_export.py -v
```
Résultat attendu : `ImportError`

- [ ] **Étape 3 : Implémenter `src/audio_export.py`**

```python
from src.story_schema import Story


def generate_audio_list(story: Story, output_path: str) -> None:
    lines = []
    for node in story.nodes:
        lines.append(f"# Fichier : {node.id}.ogg")
        lines.append(node.text.strip())
        lines.append("")  # ligne vide entre entrées

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
```

- [ ] **Étape 4 : Exécuter les tests**

```bash
pytest tests/test_audio_export.py -v
```
Résultat attendu : tous les tests PASS

- [ ] **Étape 5 : Commit**

```bash
git add src/audio_export.py tests/test_audio_export.py
git commit -m "feat: génération de la liste audio pour synthèse TTS"
```

---

## Tâche 7 : Constructeur de pack STUdio (`src/studio_format.py`)

> ⚠️ **Avant de commencer cette tâche**, consulte les notes de la Tâche 1 (`docs/studio_format_notes.md`). Le format `story.json` ci-dessous est une base à valider et corriger selon le vrai format exporté par ton installation STUdio.

**Fichiers :**
- Créer : `src/studio_format.py`
- Créer : `tests/test_studio_format.py`

- [ ] **Étape 1 : Écrire les tests**

Créer `tests/test_studio_format.py` :
```python
import os, zipfile, json, tempfile
import pytest
from src.story_schema import load_story, validate_story
from src.studio_format import build_pack, MissingAudioError

FIXTURE = "tests/fixtures/valid_story.yaml"

def load_and_validate():
    story = load_story(FIXTURE)
    validate_story(story)
    return story

def test_build_pack_creates_zip():
    story = load_and_validate()
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = os.path.join(tmpdir, "assets")
        os.makedirs(assets_dir)
        # Créer de faux fichiers audio pour le test
        for node in story.nodes:
            with open(os.path.join(assets_dir, f"{node.id}.ogg"), "wb") as f:
                f.write(b"fake_audio")
        out_zip = os.path.join(tmpdir, "pack.zip")
        build_pack(story, assets_dir, out_zip)
        assert os.path.exists(out_zip)
        assert zipfile.is_zipfile(out_zip)

def test_build_pack_contains_story_json():
    story = load_and_validate()
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = os.path.join(tmpdir, "assets")
        os.makedirs(assets_dir)
        for node in story.nodes:
            with open(os.path.join(assets_dir, f"{node.id}.ogg"), "wb") as f:
                f.write(b"fake_audio")
        out_zip = os.path.join(tmpdir, "pack.zip")
        build_pack(story, assets_dir, out_zip)
        with zipfile.ZipFile(out_zip) as z:
            assert "story.json" in z.namelist()

def test_build_pack_story_json_valid():
    story = load_and_validate()
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = os.path.join(tmpdir, "assets")
        os.makedirs(assets_dir)
        for node in story.nodes:
            with open(os.path.join(assets_dir, f"{node.id}.ogg"), "wb") as f:
                f.write(b"fake_audio")
        out_zip = os.path.join(tmpdir, "pack.zip")
        build_pack(story, assets_dir, out_zip)
        with zipfile.ZipFile(out_zip) as z:
            data = json.loads(z.read("story.json"))
        assert "title" in data
        assert "stageNodes" in data
        assert "actionNodes" in data

def test_build_pack_stage_nodes_count():
    story = load_and_validate()
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = os.path.join(tmpdir, "assets")
        os.makedirs(assets_dir)
        for node in story.nodes:
            with open(os.path.join(assets_dir, f"{node.id}.ogg"), "wb") as f:
                f.write(b"fake_audio")
        out_zip = os.path.join(tmpdir, "pack.zip")
        build_pack(story, assets_dir, out_zip)
        with zipfile.ZipFile(out_zip) as z:
            data = json.loads(z.read("story.json"))
        # Un stageNode par nœud YAML
        assert len(data["stageNodes"]) == len(story.nodes)

def test_build_pack_action_nodes_for_choices():
    story = load_and_validate()
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = os.path.join(tmpdir, "assets")
        os.makedirs(assets_dir)
        for node in story.nodes:
            with open(os.path.join(assets_dir, f"{node.id}.ogg"), "wb") as f:
                f.write(b"fake_audio")
        out_zip = os.path.join(tmpdir, "pack.zip")
        build_pack(story, assets_dir, out_zip)
        with zipfile.ZipFile(out_zip) as z:
            data = json.loads(z.read("story.json"))
        # Un actionNode pour chaque nœud qui a des choix
        nodes_with_choices = [n for n in story.nodes if n.choices]
        assert len(data["actionNodes"]) == len(nodes_with_choices)

def test_build_pack_contains_audio_files():
    story = load_and_validate()
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = os.path.join(tmpdir, "assets")
        os.makedirs(assets_dir)
        for node in story.nodes:
            with open(os.path.join(assets_dir, f"{node.id}.ogg"), "wb") as f:
                f.write(b"fake_audio")
        out_zip = os.path.join(tmpdir, "pack.zip")
        build_pack(story, assets_dir, out_zip)
        with zipfile.ZipFile(out_zip) as z:
            names = z.namelist()
        assert "assets/intro.ogg" in names

def test_build_pack_raises_if_audio_missing():
    from src.studio_format import MissingAudioError
    story = load_and_validate()
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = os.path.join(tmpdir, "assets")
        os.makedirs(assets_dir)
        # Ne pas créer les fichiers audio
        out_zip = os.path.join(tmpdir, "pack.zip")
        with pytest.raises(MissingAudioError):
            build_pack(story, assets_dir, out_zip)
```

- [ ] **Étape 2 : Exécuter les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_studio_format.py -v
```
Résultat attendu : `ImportError`

- [ ] **Étape 3 : Implémenter `src/studio_format.py`**

> ⚠️ Valider le format `story.json` avec les notes de la Tâche 1 avant de finaliser.

```python
import json
import os
import uuid
import zipfile
from src.story_schema import Story, Node


class MissingAudioError(Exception):
    pass


def _new_uuid() -> str:
    return str(uuid.uuid4())


def build_pack(story: Story, assets_dir: str, output_zip: str) -> None:
    """Construit un pack ZIP importable dans STUdio."""

    # Vérifier que tous les fichiers audio sont présents
    missing = []
    for node in story.nodes:
        audio_path = os.path.join(assets_dir, f"{node.id}.ogg")
        if not os.path.exists(audio_path):
            missing.append(f"{node.id}.ogg")
    if missing:
        raise MissingAudioError(
            f"Fichiers audio manquants dans {assets_dir} :\n" +
            "\n".join(f"  - {m}" for m in missing)
        )

    # Assigner un UUID à chaque nœud YAML
    node_uuids = {node.id: _new_uuid() for node in story.nodes}
    action_uuids = {node.id: _new_uuid() for node in story.nodes if node.choices}

    stage_nodes = []
    action_nodes = []

    for node in story.nodes:
        stage_uuid = node_uuids[node.id]
        has_choices = bool(node.choices)

        ok_transition = None
        if has_choices:
            ok_transition = {
                "actionNode": action_uuids[node.id],
                "optionIndex": 0,
            }

        stage_nodes.append({
            "uuid": stage_uuid,
            "type": "stage",
            "name": node.id,
            "audio": f"assets/{node.id}.ogg",
            "image": None,
            "okTransition": ok_transition,
            "homeTransition": None,
            "controlSettings": {
                "wheel": has_choices,
                "ok": has_choices,
                "home": not has_choices,
                "pause": False,
                "autoplay": False,
            },
        })

        if has_choices:
            options = [
                {"stageNode": node_uuids[choice.next]}
                for choice in node.choices
            ]
            action_nodes.append({
                "uuid": action_uuids[node.id],
                "name": f"action_{node.id}",
                "options": options,
            })

    story_json = {
        "format": "v1",
        "title": story.title,
        "version": story.version,
        "description": "",
        "thumbnail": None,
        "age": [6, 12],
        "stageNodes": stage_nodes,
        "actionNodes": action_nodes,
    }

    # Assembler le ZIP
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("story.json", json.dumps(story_json, ensure_ascii=False, indent=2))
        for node in story.nodes:
            audio_path = os.path.join(assets_dir, f"{node.id}.ogg")
            zf.write(audio_path, f"assets/{node.id}.ogg")
```

- [ ] **Étape 4 : Exécuter les tests**

```bash
pytest tests/test_studio_format.py -v
```
Résultat attendu : tous les tests PASS

- [ ] **Étape 5 : Commit**

```bash
git add src/studio_format.py tests/test_studio_format.py
git commit -m "feat: constructeur de pack STUdio (story.json + ZIP)"
```

---

## Tâche 8 : CLI générateur de pack (`generate_pack.py`)

**Fichiers :**
- Créer : `generate_pack.py`

- [ ] **Étape 1 : Implémenter `generate_pack.py`**

```python
#!/usr/bin/env python3
"""Générateur de pack STUdio à partir d'un story.yaml."""
import sys
import os
from src.story_schema import load_story, validate_story, StoryValidationError
from src.audio_export import generate_audio_list
from src.studio_format import build_pack, MissingAudioError


def main():
    if len(sys.argv) < 2:
        print("Usage : python generate_pack.py <story.yaml>")
        sys.exit(1)

    yaml_path = sys.argv[1]
    if not os.path.exists(yaml_path):
        print(f"❌ Fichier introuvable : {yaml_path}")
        sys.exit(1)

    print(f"\n📖 Lecture de {yaml_path}...")
    try:
        story = load_story(yaml_path)
    except Exception as e:
        print(f"❌ Erreur de lecture YAML : {e}")
        sys.exit(1)

    print(f"   → {len(story.nodes)} nœuds, {len(story.characters)} personnages")

    # Validation
    try:
        validate_story(story)
        print("   → ✅ Validation OK")
    except StoryValidationError as e:
        print(f"❌ Histoire invalide : {e}")
        sys.exit(1)

    # Dossier de sortie basé sur le nom du fichier YAML
    base_name = os.path.splitext(os.path.basename(yaml_path))[0]
    assets_dir = "assets"
    audio_list_path = f"{base_name}_audio_to_synthesize.txt"
    output_zip = f"{base_name}_pack.zip"

    # Étape 1 : Liste audio
    print(f"\n📋 Génération de la liste audio → {audio_list_path}")
    generate_audio_list(story, audio_list_path)
    print(f"   → ✅ {len(story.nodes)} fichiers audio à synthétiser")
    print(f"   → Ouvre {audio_list_path} et synthétise les voix dans ElevenLabs/Murf")
    print(f"   → Place les .ogg dans le dossier : {assets_dir}/")

    # Étape 2 : Vérification des assets
    print(f"\n🔍 Vérification des fichiers audio dans {assets_dir}/...")
    missing = []
    os.makedirs(assets_dir, exist_ok=True)
    for node in story.nodes:
        audio_path = os.path.join(assets_dir, f"{node.id}.ogg")
        if not os.path.exists(audio_path):
            missing.append(f"{node.id}.ogg")

    if missing:
        print(f"   → ⏳ {len(missing)} fichiers audio manquants :")
        for m in missing[:10]:
            print(f"      - {m}")
        if len(missing) > 10:
            print(f"      ... et {len(missing) - 10} autres")
        print(f"\n💡 Synthétise les voix puis relance : python generate_pack.py {yaml_path}")
        sys.exit(0)

    print(f"   → ✅ {len(story.nodes)}/{len(story.nodes)} fichiers présents")

    # Étape 3 : Construction du pack
    print(f"\n📦 Construction du pack STUdio → {output_zip}")
    try:
        build_pack(story, assets_dir, output_zip)
    except MissingAudioError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"   → ✅ Pack créé : {output_zip}")
    print(f"\n🎉 Prêt ! Importe {output_zip} dans STUdio puis transfère sur la Flam.")


if __name__ == "__main__":
    main()
```

- [ ] **Étape 2 : Tester avec la liste audio uniquement (sans fichiers .ogg)**

```bash
python generate_pack.py tests/fixtures/valid_story.yaml
```
Résultat attendu : génère `valid_story_audio_to_synthesize.txt` et indique les fichiers manquants, puis s'arrête proprement.

- [ ] **Étape 3 : Tester avec de faux fichiers audio**

```bash
# Créer de faux fichiers audio pour tester le pack
python -c "
import os
from src.story_schema import load_story
story = load_story('tests/fixtures/valid_story.yaml')
os.makedirs('assets', exist_ok=True)
for n in story.nodes:
    with open(f'assets/{n.id}.ogg', 'wb') as f: f.write(b'fake')
print('Faux audios créés')
"
python generate_pack.py tests/fixtures/valid_story.yaml
```
Résultat attendu : `valid_story_pack.zip` créé sans erreur.

- [ ] **Étape 4 : Vérifier le ZIP manuellement**

```bash
python -c "
import zipfile
with zipfile.ZipFile('valid_story_pack.zip') as z:
    print('\n'.join(z.namelist()))
"
```
Résultat attendu : `story.json` + `assets/intro.ogg` + tous les autres nœuds.

- [ ] **Étape 5 : Nettoyer les faux fichiers de test**

```bash
# Supprimer les faux audios et le pack de test
python -c "
import os, glob
for f in glob.glob('assets/*.ogg'): os.remove(f)
if os.path.exists('valid_story_pack.zip'): os.remove('valid_story_pack.zip')
if os.path.exists('valid_story_audio_to_synthesize.txt'): os.remove('valid_story_audio_to_synthesize.txt')
print('Nettoyage OK')
"
```

- [ ] **Étape 6 : Lancer la suite de tests complète**

```bash
pytest tests/ -v
```
Résultat attendu : tous les tests PASS

- [ ] **Étape 7 : Commit final**

```bash
git add generate_pack.py
git commit -m "feat: CLI generate_pack.py — validation, liste audio, pack STUdio"
```

---

## Tâche 9 : Test de bout en bout avec une vraie histoire

- [ ] **Étape 1 : Créer l'histoire pilote via le wizard**

```bash
python create_story.py
```

Répondre avec des données réelles (univers, personnages, lieu, danger, objectif). L'histoire sera sauvegardée dans `stories/`.

- [ ] **Étape 2 : Affiner les textes**

Ouvrir le fichier YAML généré dans un éditeur et réécrire les textes placeholder avec la vraie narration.

- [ ] **Étape 3 : Valider l'histoire affinée**

```bash
python generate_pack.py stories/<nom_histoire>.yaml
```
Résultat attendu : génère le fichier `<nom>_audio_to_synthesize.txt` et confirme la structure valide.

- [ ] **Étape 4 : Synthétiser les voix**

- Ouvrir `<nom>_audio_to_synthesize.txt`
- Pour chaque entrée, copier le texte dans ElevenLabs ou Murf
- Télécharger le fichier audio en `.ogg` et le nommer exactement comme indiqué
- Placer tous les `.ogg` dans `assets/`

- [ ] **Étape 5 : Générer le pack final**

```bash
python generate_pack.py stories/<nom_histoire>.yaml
```
Résultat attendu : `<nom>_pack.zip` créé.

- [ ] **Étape 6 : Importer dans STUdio et tester**

- Ouvrir STUdio
- Importer le fichier `<nom>_pack.zip`
- Parcourir l'histoire dans STUdio pour vérifier la navigation
- Si des ajustements du format sont nécessaires, noter les divergences et corriger `src/studio_format.py`

- [ ] **Étape 7 : Transférer sur la Flam**

- Connecter la Flam en USB
- Transférer depuis STUdio
- Tester l'histoire sur le vrai appareil

- [ ] **Étape 8 : Commit**

```bash
git add stories/
git commit -m "feat: histoire pilote ajoutée"
```

---

## Récapitulatif des commandes

```bash
# Créer une nouvelle histoire
python create_story.py

# Générer la liste audio (avant d'avoir les .ogg)
python generate_pack.py stories/mon_histoire.yaml

# Générer le pack final (après avoir placé les .ogg dans assets/)
python generate_pack.py stories/mon_histoire.yaml

# Lancer les tests
pytest tests/ -v
```
