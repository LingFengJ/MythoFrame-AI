"""Project creation and validation."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from mythoframe.schemas import PROJECT_DIRS, PROJECT_FILES


@dataclass(frozen=True)
class ProjectSpec:
    slug: str
    title: str
    aspect_ratio: str = "16:9"
    runtime: str = "60-90 seconds"
    source_type: str = "to_be_determined"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    if not slug:
        raise ValueError("Project slug cannot be empty.")
    return slug


def project_dir(root: Path, slug: str) -> Path:
    return root / "projects" / slugify(slug)


def init_project(root: Path, spec: ProjectSpec, force: bool = False) -> list[Path]:
    path = project_dir(root, spec.slug)
    written: list[Path] = []

    for relative in PROJECT_DIRS:
        (path / relative).mkdir(parents=True, exist_ok=True)

    templates = _project_templates(spec)
    for filename, content in templates.items():
        target = path / filename
        if target.exists() and not force:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        written.append(target)

    return written


def validate_project(path: Path) -> list[str]:
    problems: list[str] = []
    if not path.exists():
        return [f"Project directory does not exist: {path}"]

    for filename in PROJECT_FILES:
        target = path / filename
        if not target.exists():
            problems.append(f"Missing file: {target}")

    for relative in PROJECT_DIRS:
        target = path / relative
        if not target.exists():
            problems.append(f"Missing directory: {target}")

    for filename in ("project_bible.json", "characters.json", "edit_plan.json"):
        target = path / filename
        if target.exists():
            try:
                json.loads(target.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                problems.append(f"Invalid JSON in {target}: {exc}")

    return problems


def _project_templates(spec: ProjectSpec) -> dict[str, str]:
    bible = {
        "project": {
            "slug": slugify(spec.slug),
            "title": spec.title,
            "aspect_ratio": spec.aspect_ratio,
            "runtime": spec.runtime,
            "source_type": spec.source_type,
            "status": "planning",
        },
        "creative_direction": {
            "visual_style": "to_be_determined",
            "tone": "cinematic",
            "language": "to_be_determined",
            "rights_status": "to_be_determined",
        },
        "generation_policy": {
            "default_mode": "manual_file",
            "api_is_opt_in": True,
            "notes": (
                "Use manual_file or codex_web by default. Use api_command only "
                "when the user explicitly configures an API wrapper."
            ),
        },
    }

    characters = {
        "characters": [],
        "consistency_rules": [
            "Lock face, hair, costume, palette, and accessories before shot generation.",
            "Use reference images whenever the selected image tool supports them.",
            "Repeat core identity traits in every shot prompt if reference images are unavailable.",
        ],
    }

    edit_plan = {
        "timeline": {
            "aspect_ratio": spec.aspect_ratio,
            "runtime": spec.runtime,
            "frame_rate": "to_be_determined",
        },
        "tracks": {
            "video": [],
            "dialogue": [],
            "narration": [],
            "music": [],
            "sound_effects": [],
            "subtitles": [],
        },
        "automation": {
            "rough_cut": "planned",
            "final_review_required": True,
        },
    }

    return {
        "project_bible.json": _json(bible),
        "characters.json": _json(characters),
        "script.md": _script_template(spec),
        "shot_table.csv": _csv(
            [
                "shot_number",
                "duration",
                "camera_movement",
                "framing",
                "visual_description",
                "image_prompt",
                "video_prompt",
                "dialogue",
                "narration",
                "music",
                "sound_effects",
                "review_status",
            ]
        ),
        "image_prompts.csv": _csv(
            [
                "shot_number",
                "candidate_id",
                "prompt",
                "reference_assets",
                "negative_prompt",
                "status",
                "selected_asset",
            ]
        ),
        "video_prompts.csv": _csv(
            [
                "shot_number",
                "source_image",
                "prompt",
                "duration",
                "status",
                "selected_clip",
            ]
        ),
        "voice_lines.csv": _csv(
            [
                "line_id",
                "shot_number",
                "speaker",
                "text",
                "voice_style",
                "status",
                "audio_asset",
            ]
        ),
        "sound_plan.csv": _csv(
            [
                "cue_id",
                "shot_number",
                "cue_type",
                "description",
                "timing",
                "status",
                "audio_asset",
            ]
        ),
        "edit_plan.json": _json(edit_plan),
    }


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _csv(headers: list[str]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    return buffer.getvalue()


def _script_template(spec: ProjectSpec) -> str:
    return (
        f"# {spec.title}\n\n"
        "## Source\n\n"
        "- Source type: to be determined\n"
        "- Rights status: to be determined\n\n"
        "## Short Structure\n\n"
        "- Target aspect ratio: 16:9 horizontal\n"
        "- Target runtime: 60-90 seconds\n"
        "- Scene goal: to be determined\n"
        "- Emotional arc: to be determined\n\n"
        "## Draft Script\n\n"
        "To be generated.\n"
    )

