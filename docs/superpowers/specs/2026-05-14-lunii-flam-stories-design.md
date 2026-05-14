# Design : Créateur d'histoires interactives pour Lunii Flam

**Date :** 2026-05-14  
**Contexte :** Créer des histoires interactives personnalisées pour la boîte à histoires Lunii Flam d'une enfant de 9 ans, univers animaux/aventure/nature.

---

## Objectif

Produire un système en deux scripts **Python 3.8+** permettant de :
1. Guider la création d'une histoire interactive (assistant CLI)
2. Générer un pack prêt à importer dans STUdio (outil Lunii open-source déjà installé)

L'approche est : **une histoire pilote d'abord, puis un système réutilisable** pour en créer d'autres facilement.

---

## Caractéristiques de l'histoire cible

- **Public :** enfant de 9 ans
- **Univers :** animaux, nature, aventure, magie, sorcières
- **Durée :** 10-15 minutes d'écoute
- **Interactivité :**
  - Choix du personnage jouable au départ (2-4 animaux)
  - 3 à 6 moments de choix moraux ou stratégiques en cours de route
  - **Maximum 3 choix par nœud** (contrainte physique : la Flam navigue via molette/boutons)
- **Volume textuel :** 1 800 à 2 500 mots répartis sur 60-80 nœuds
- **Audio :** voix synthétisées via ElevenLabs ou Murf (fichiers `.ogg`)

---

## Architecture

```
create_story.py          →  story.yaml  →  generate_pack.py
(assistant CLI)             (histoire)     (générateur STUdio)
                                │
                                ├── audio_to_synthesize.txt
                                └── pack/
                                     ├── story.json
                                     └── assets/*.ogg
                                              │
                                     [Import STUdio → Flam]
```

---

## Composant 1 : `create_story.py` — Assistant d'écriture

Script CLI interactif qui guide l'auteur avec des questions simples, puis génère un `story.yaml` complet avec des textes narratifs développés (4-8 phrases par nœud).

### Questions posées

1. Titre de l'histoire
2. Nombre de personnages jouables (2-4) et leurs noms
3. Lieu de départ
4. Danger/obstacle principal
5. Objectif à atteindre
6. Nombre de moments de choix (3-6)

### Sortie générée

Un fichier `story.yaml` contenant :
- Les métadonnées (titre, version, durée estimée)
- La liste des personnages avec leurs IDs
- L'arbre complet de nœuds : introduction → sélection du personnage → actes → fins multiples
- Des textes narratifs de placeholder cohérents avec les paramètres saisis, déjà développés et prêts à être affinés

### Structure de l'arbre généré

```
intro (choix du personnage)
├── personnage_1_depart
│   ├── acte1_choix1_a  ──► acte2_choix2_a ──► fin_victoire_1a
│   │                   └─► acte2_choix2_b ──► fin_victoire_1b
│   └── acte1_choix1_b  ──► ...
├── personnage_2_depart
│   └── ...
└── personnage_N_depart
    └── ...
```

Chaque personnage a son propre arbre de branches, avec au moins une fin heureuse et une fin alternative (pas forcément négative, mais différente).

---

## Composant 2 : `generate_pack.py` — Générateur de pack STUdio

Script Python qui transforme un `story.yaml` finalisé en pack importable dans STUdio.

### Étapes d'exécution

1. **Validation** : lecture et vérification de `story.yaml` (nœuds orphelins, liens cassés, IDs dupliqués)
2. **Génération audio list** : production de `audio_to_synthesize.txt` avec le texte de chaque nœud et le nom de fichier `.ogg` attendu
3. **Vérification assets** : contrôle que tous les fichiers `.ogg` sont présents dans `assets/`
4. **Construction pack** : génération de `story.json` au format STUdio + assemblage du ZIP final

### Format de `audio_to_synthesize.txt`

```
# Fichier : intro.ogg
[texte complet du nœud intro]

# Fichier : aigle_depart.ogg
[texte complet du nœud aigle_depart]
...
```

### Format du pack STUdio

- `story.json` : graphe de nœuds avec transitions, métadonnées compatibles Flam
- `assets/` : fichiers `.ogg` référencés dans le graphe
- Archive `.zip` finale prête à importer dans STUdio

> **Note d'implémentation :** Le format exact de `story.json` (structure du graphe, champs requis, version du schéma Flam) doit être déterminé lors de l'implémentation en inspectant le code source de STUdio (GitHub : marian-m12l/studio) et en exportant un pack existant comme référence.

---

## Format YAML de l'histoire

```yaml
title: "Titre de l'histoire"
version: 1
duration_min: 12

characters:
  - id: aigle
    name: "Aigle"
  - id: hirondelle
    name: "Hirondelle"

nodes:
  - id: intro
    text: >
      Texte narratif développé (4-8 phrases)...
    choices:
      - label: "L'Aigle"
        next: aigle_depart
      - label: "L'Hirondelle"
        next: hirondelle_depart

  - id: aigle_depart
    character: aigle
    text: >
      ...
    choices:
      - label: "Option A"
        next: noeud_suivant_a
      - label: "Option B"
        next: noeud_suivant_b

  - id: fin_aigle_victoire
    character: aigle
    text: >
      Texte de fin...
    choices: []
```

**Règles :**
- `choices: []` = fin de branche
- `character` est optionnel sur les nœuds partagés
- Les IDs sont en snake_case et uniques dans le fichier

---

## Pipeline de travail complet

1. `python create_story.py` → répondre aux questions → `story.yaml` généré
2. Ouvrir `story.yaml` et affiner les textes
3. `python generate_pack.py story.yaml` → `audio_to_synthesize.txt` produit
4. Synthétiser les voix sur ElevenLabs/Murf, placer les `.ogg` dans `assets/`
5. `python generate_pack.py story.yaml` → pack `.zip` final produit
6. Importer dans STUdio → tester → transférer sur la Flam

---

## Périmètre hors-scope

- Interface graphique (tout est CLI)
- Génération automatique des fichiers audio (synthèse manuelle via ElevenLabs/Murf)
- Images/illustrations (audio uniquement, compatible Flam)
- Traduction multilingue
