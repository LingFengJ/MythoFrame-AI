"""Project creation and validation."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

from mythoframe.schemas import (
    ARTIFACT_STATUSES,
    CSV_INTEGER_FIELDS,
    CSV_REQUIRED_HEADERS,
    CSV_REQUIRED_ROW_FIELDS,
    CSV_STATUS_FIELDS,
    PROJECT_DIRS,
    PROJECT_FILES,
    SOUND_CUE_TYPES,
)


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
                value = json.loads(target.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                problems.append(f"Invalid JSON in {target}: {exc}")
                continue
            problems.extend(_validate_json_shape(target, value))

    csv_rows_by_file: dict[str, list[dict[str, str]]] = {}
    for filename, expected_headers in CSV_REQUIRED_HEADERS.items():
        target = path / filename
        if target.exists():
            csv_problems, rows = _validate_csv(target, expected_headers)
            problems.extend(csv_problems)
            csv_rows_by_file[filename] = rows

    problems.extend(_validate_cross_artifact_rows(path, csv_rows_by_file))

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
        "clips": [],
        "audio": {
            "dialogue": [],
            "narration": [],
            "music": [],
            "sound_effects": [],
        },
        "subtitles": [],
        "review_gates": ["pacing", "continuity", "audio balance", "caption timing"],
        "automation": {
            "rough_cut": "planned",
            "final_review_required": True,
        },
    }

    return {
        "source_brief.md": _source_brief_template(spec),
        "adaptation.md": _placeholder_doc(spec.title, "Adaptation"),
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


def _source_brief_template(spec: ProjectSpec) -> str:
    return (
        f"# {spec.title} Source Brief\n\n"
        "## Source\n\n"
        f"- Source type: {spec.source_type}\n"
        "- Rights status: to_be_determined\n"
        "- Source title: to_be_determined\n"
        "- Source excerpt or scene summary: to_be_determined\n\n"
        "## Target\n\n"
        f"- Aspect ratio: {spec.aspect_ratio}\n"
        f"- Runtime: {spec.runtime}\n"
        "- Language: to_be_determined\n"
        "- Audience: to_be_determined\n"
        "- Visual style: to_be_determined\n"
        "- Emotional tone: cinematic\n\n"
        "## Creative Constraints\n\n"
        "- Must include: to_be_determined\n"
        "- Must avoid: to_be_determined\n"
        "- Character consistency notes: to_be_determined\n"
        "- Sound direction: to_be_determined\n"
    )


def _placeholder_doc(title: str, artifact: str) -> str:
    return f"# {title} {artifact}\n\nTo be generated and reviewed.\n"


def _validate_json_shape(path: Path, value: object) -> list[str]:
    problems: list[str] = []
    name = path.name
    if not isinstance(value, dict):
        return [f"Expected JSON object in {path}"]

    if name == "project_bible.json":
        for key in ("project", "creative_direction", "generation_policy"):
            if key not in value:
                problems.append(f"Missing key `{key}` in {path}")
    elif name == "characters.json":
        characters = value.get("characters")
        if not isinstance(characters, list):
            problems.append(f"Expected `characters` list in {path}")
        else:
            for index, character in enumerate(characters, start=1):
                if not isinstance(character, dict):
                    problems.append(f"Expected character {index} to be an object in {path}")
                    continue
                for key in ("id", "name", "reference_prompt", "consistency_prompt"):
                    if not character.get(key):
                        problems.append(f"Missing `{key}` for character {index} in {path}")
    elif name == "edit_plan.json":
        if not isinstance(value.get("timeline"), dict):
            problems.append(f"Expected `timeline` object in {path}")
        if not isinstance(value.get("clips"), list):
            problems.append(f"Expected `clips` list in {path}")
        audio = value.get("audio")
        if not isinstance(audio, dict):
            problems.append(f"Expected `audio` object in {path}")
        else:
            for key in ("dialogue", "narration", "music", "sound_effects"):
                if not isinstance(audio.get(key), list):
                    problems.append(f"Expected `audio.{key}` list in {path}")
        if not isinstance(value.get("subtitles"), list):
            problems.append(f"Expected `subtitles` list in {path}")
        if not isinstance(value.get("review_gates"), list):
            problems.append(f"Expected `review_gates` list in {path}")
    return problems


def _validate_csv(
    path: Path,
    expected_headers: tuple[str, ...],
) -> tuple[list[str], list[dict[str, str]]]:
    problems: list[str] = []
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        try:
            headers = reader.fieldnames
        except csv.Error as exc:
            return [f"Unable to parse CSV in {path}: {exc}"], []

        if headers is None:
            return [f"Missing CSV header row in {path}"], []

        if tuple(headers) != expected_headers:
            problems.append(
            f"Unexpected CSV headers in {path}: expected {list(expected_headers)}, got {headers}"
            )
            return problems, []

        for row_number, row in enumerate(reader, start=2):
            normalized = {key: (value or "").strip() for key, value in row.items()}
            if not any(normalized.values()):
                continue
            rows.append(normalized)
            problems.extend(_validate_csv_row(path, row_number, normalized))

    return problems, rows


def _validate_csv_row(path: Path, row_number: int, row: dict[str, str]) -> list[str]:
    problems: list[str] = []
    filename = path.name

    for field in CSV_REQUIRED_ROW_FIELDS.get(filename, ()):
        if not row.get(field):
            problems.append(f"Missing `{field}` in {path} row {row_number}")

    for field in CSV_INTEGER_FIELDS.get(filename, ()):
        value = row.get(field)
        if value and not value.isdigit():
            problems.append(f"Expected integer `{field}` in {path} row {row_number}, got {value!r}")

    for field in CSV_STATUS_FIELDS.get(filename, ()):
        value = row.get(field)
        if value and value not in ARTIFACT_STATUSES:
            allowed = ", ".join(ARTIFACT_STATUSES)
            problems.append(
                f"Invalid `{field}` in {path} row {row_number}: {value!r}; expected one of {allowed}"
            )

    if filename in ("shot_table.csv", "video_prompts.csv"):
        duration = row.get("duration")
        if duration and not re.fullmatch(r"\d+(?:\.\d+)?s", duration):
            problems.append(
                f"Expected duration like `3s` or `2.5s` in {path} row {row_number}, got {duration!r}"
            )

    if filename == "sound_plan.csv":
        cue_type = row.get("cue_type")
        if cue_type and cue_type not in SOUND_CUE_TYPES:
            allowed = ", ".join(SOUND_CUE_TYPES)
            problems.append(
                f"Invalid `cue_type` in {path} row {row_number}: {cue_type!r}; expected one of {allowed}"
            )

    return problems


def _validate_cross_artifact_rows(
    path: Path,
    csv_rows_by_file: dict[str, list[dict[str, str]]],
) -> list[str]:
    problems: list[str] = []
    shot_rows = csv_rows_by_file.get("shot_table.csv", [])
    shot_numbers = {row["shot_number"] for row in shot_rows if row.get("shot_number", "").isdigit()}
    if not shot_numbers:
        return problems

    for filename in ("image_prompts.csv", "video_prompts.csv", "voice_lines.csv", "sound_plan.csv"):
        for index, row in enumerate(csv_rows_by_file.get(filename, []), start=2):
            shot_number = row.get("shot_number")
            if shot_number and shot_number.isdigit() and shot_number not in shot_numbers:
                problems.append(
                    f"Unknown shot_number {shot_number!r} in {path / filename} row {index}"
                )

    return problems
