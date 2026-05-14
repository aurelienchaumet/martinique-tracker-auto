# STUdio Pack Format — Research Notes

**Source:** marian-m12l/studio (GitHub), o-daneel/Lunii.QT, jersou/studio-pack-generator  
**Date:** 2026-05-14

---

## 1. Overview

STUdio is an open-source community tool that reads, creates, and transfers story packs
to/from Lunii devices. Custom packs are distributed as **ZIP archives** importable
directly into the STUdio interface (drag-and-drop or file open).

Repository: https://github.com/marian-m12l/studio

---

## 2. ZIP Archive Layout

```
my_story.zip
├── story.json        ← required — full pack descriptor
├── thumbnail.png     ← optional — pack cover shown in STUdio UI
└── assets/           ← required — all image and audio files
    ├── <sha1>.png
    ├── <sha1>.mp3
    └── ...
```

### Asset naming
Assets are named **SHA-1 hash of their binary content** + the original extension.  
Example: `a3f8c21b9e4d….mp3`

This means two identical files automatically share a single asset entry (deduplication).

---

## 3. story.json Structure

```json
{
  "version": 1,
  "title": "My Story Title",
  "description": "Optional description",
  "nightModeAvailable": false,
  "stageNodes": [ ... ],
  "actionNodes": [ ... ]
}
```

### 3.1 StageNode

A StageNode plays audio and/or shows an image. It can trigger transitions on button presses.

```json
{
  "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "squareOne": true,
  "image": "a3f8c21b.png",
  "audio": "b7d2e94f.mp3",
  "okTransition": {
    "actionNode": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
    "optionIndex": 0
  },
  "homeTransition": {
    "actionNode": "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
    "optionIndex": 0
  },
  "controlSettings": {
    "wheel": true,
    "ok": true,
    "home": true,
    "pause": false,
    "autoplay": false
  },
  "name": "Human-readable label (optional)",
  "type": "stage",
  "groupId": "optional-group-uuid",
  "position": { "x": 100, "y": 200 }
}
```

Key fields:
- `uuid` — unique identifier (UUID v4 string)
- `squareOne` — `true` only for the **root/entry** node of the pack
- `image` — filename in `assets/` or `null`
- `audio` — filename in `assets/` or `null`
- `okTransition` — triggered when the child presses OK; references an ActionNode UUID + which option index to preselect
- `homeTransition` — triggered when the child presses HOME
- `controlSettings` — which physical controls are active on this node

### 3.2 ActionNode

An ActionNode is a **menu**: a list of StageNode UUIDs the user can navigate with the wheel.

```json
{
  "id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
  "options": [
    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  ],
  "name": "Human-readable label (optional)",
  "type": "action",
  "groupId": "optional-group-uuid",
  "position": { "x": 300, "y": 200 }
}
```

Key fields:
- `id` — unique identifier (UUID v4 string)
- `options` — **ordered** list of StageNode UUIDs; the wheel cycles through them

### 3.3 Graph rules (critical)

```
StageNode  →(okTransition / homeTransition)→  ActionNode
ActionNode →(options[i])→                     StageNode
```

- A StageNode can **only** transition to an ActionNode.
- An ActionNode contains **only** StageNode UUIDs in its options list.
- The tree root is always a StageNode with `squareOne: true`.
- Transitions reference an ActionNode's UUID + an `optionIndex` to pre-position the wheel.

---

## 4. Media Format Requirements

### Images
| Property | Value |
|----------|-------|
| Formats  | PNG, JPEG, BMP (24-bit) |
| Dimensions | **320 × 240 pixels** (exact) |
| Color space | RGB |

### Audio
| Property | Value |
|----------|-------|
| Formats  | MP3, OGG/Vorbis, WAV (signed 16-bit, mono, 32000 Hz) |
| Sample rate (MP3/OGG) | **44100 Hz** |
| Channels | Mono recommended |
| Peak normalization | 0 dB |

OGG/Vorbis is the preferred format for custom packs (smaller size, good quality).  
WAV must be signed 16-bit, mono, 32000 Hz.

---

## 5. FLAM Device — Important Notes

**FLAM is NOT natively supported by STUdio.** Key findings:

- Official Lunii support page states: *"My Lunii Studio is not compatible with FLAM."*
- FLAM uses a **proprietary encrypted format** (undocumented):
  - Archive: `story_name.8B_UUID.zip` with encryption key
  - Internal files: `main.lsf` scripts, `.lif` image files, `.mp3` + `.mp3map` audio metadata
  - Encryption: uses a Story Key (algorithm not publicly known)
- The format of original FLAM stories "remains unknown" per community reverse-engineering efforts.

### Practical approach for this project

Since STUdio accepts standard ZIP packs and can transfer them to Lunii devices, and since
FLAM can import Lunii stories (via third-party tools like Lunii.QT, with firmware v2.x.x),
the recommended strategy is:

1. **Generate STUdio-format ZIP packs** (this project's target) — works natively in STUdio
2. The user can then transfer the pack to their Flam via STUdio if STUdio adds Flam support,
   or via Lunii.QT (https://github.com/o-daneel/Lunii.QT) as an intermediary.

**Conclusion:** `generate_pack.py` should target the STUdio archive format (story.json in ZIP).
FLAM encryption is out of scope and likely not achievable without the proprietary key.

---

## 6. Node Type Presets (STUdio UI shortcuts)

STUdio provides shortcut node types in its UI (these map to specific `controlSettings` combos):

| UI Type     | wheel | ok  | home | pause | autoplay | Notes |
|-------------|-------|-----|------|-------|----------|-------|
| Cover Node  | false | false | false | false | true  | Entry node, auto-plays |
| Menu Node   | true  | true | false | false | false | User selects with wheel |
| Story Node  | false | false | true | true  | true  | Plays through, Home to return |
| Stage Node  | —     | —   | —    | —     | —     | Expert mode, all manual |

---

## 7. Minimal Valid Pack (single linear story)

A minimal pack needs:
1. One root StageNode (`squareOne: true`) — e.g., the title/cover
2. One ActionNode pointing to the first real stage
3. N StageNodes for story content
4. N-1 ActionNodes linking story stages in sequence
5. A final StageNode with no `okTransition` (story ends)

The `homeTransition` on all nodes should typically point back to the root
ActionNode (index 0) so the child can return to the story selection.

---

## 8. References

- [STUdio GitHub](https://github.com/marian-m12l/studio)
- [STUdio Documentation Wiki](https://github.com/marian-m12l/studio/wiki/Documentation)
- [STUdio website](https://marian-m12l.github.io/studio-website/)
- [studio-pack-generator](https://github.com/jersou/studio-pack-generator)
- [Lunii.QT (FLAM support)](https://github.com/o-daneel/Lunii.QT)
- [Lunii.PACKS Python proof-of-concept](https://github.com/o-daneel/Lunii.PACKS)
- [audiotolunii](https://github.com/laruche/audiotolunii)
