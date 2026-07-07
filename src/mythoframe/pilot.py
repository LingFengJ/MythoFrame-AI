"""Pilot project scaffolding."""

from __future__ import annotations

import json
from pathlib import Path

from mythoframe.project import ProjectSpec, init_project, project_dir


PILOT_TITLE = "Pilot Scene: The Last Lantern"


def init_pilot_project(root: Path, slug: str = "pilot-scene", force: bool = False) -> Path:
    spec = ProjectSpec(
        slug=slug,
        title=PILOT_TITLE,
        aspect_ratio="16:9",
        runtime="60-90 seconds",
        source_type="original_test_scene",
    )
    init_project(root, spec, force=force)
    path = project_dir(root, slug)

    _write_source_brief(path, force=force)
    _write_project_bible(path, slug, force=force)
    return path


def _write_source_brief(path: Path, force: bool) -> None:
    target = path / "source_brief.md"
    if target.exists() and not force and "to_be_determined" not in target.read_text(encoding="utf-8"):
        return

    target.write_text(
        """# Pilot Scene: The Last Lantern Source Brief

## Source

- Source type: original_test_scene
- Rights status: original_project_test_material
- Source title: The Last Lantern
- Source excerpt or scene summary: A young courier reaches a ruined sky bridge at dusk carrying the last lit lantern in the city. A silent shadow follows from below. The courier must decide whether to use the lantern to reveal the safe path forward or send it floating into the fog as a signal for others.

## Target

- Aspect ratio: 16:9
- Runtime: 60-90 seconds
- Language: English
- Audience: general fantasy animation audience
- Visual style: cinematic fantasy animation, painterly realism, moody dusk light
- Emotional tone: quiet tension turning into hope

## Creative Constraints

- Must include: lantern light, broken sky bridge, fog, a moment of hesitation, hopeful final image
- Must avoid: explicit violence, complex crowd scenes, more than two speaking characters
- Character consistency notes: one main courier character; optional shadow presence should remain abstract
- Sound direction: wind through broken stone, distant city bells, soft lantern flame, restrained hopeful music
""",
        encoding="utf-8",
        newline="\n",
    )


def _write_project_bible(path: Path, slug: str, force: bool) -> None:
    target = path / "project_bible.json"
    if not target.exists():
        return
    bible = json.loads(target.read_text(encoding="utf-8"))
    if not force and bible.get("project", {}).get("status") != "planning":
        return

    bible["project"].update(
        {
            "slug": slug,
            "title": PILOT_TITLE,
            "aspect_ratio": "16:9",
            "runtime": "60-90 seconds",
            "source_type": "original_test_scene",
            "status": "pilot_seeded",
        }
    )
    bible["creative_direction"].update(
        {
            "visual_style": "cinematic fantasy animation, painterly realism",
            "tone": "quiet tension turning into hope",
            "language": "English",
            "rights_status": "original_project_test_material",
        }
    )
    target.write_text(json.dumps(bible, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

