"""Generated media import, selection, and missing-file checks."""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from mythoframe.assets import ASSET_TYPES, asset_path
from mythoframe.project import slugify
from mythoframe.schemas import ARTIFACT_STATUSES


MANIFEST_FILE = "asset_manifest.json"
MANIFEST_VERSION = 1


@dataclass(frozen=True)
class AssetImportResult:
    candidate_id: str
    destination: Path
    manifest_path: Path


@dataclass(frozen=True)
class AssetSelectionResult:
    candidate_id: str
    status: str
    updated_files: tuple[Path, ...]


@dataclass(frozen=True)
class MissingMedia:
    source: str
    field: str
    path: Path


def load_asset_manifest(project_path: Path) -> dict[str, object]:
    path = project_path / MANIFEST_FILE
    if not path.exists():
        return _empty_manifest()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    if data.get("version") != MANIFEST_VERSION:
        raise ValueError(f"Unsupported asset manifest version in {path}: {data.get('version')}")
    if not isinstance(data.get("candidates"), list):
        raise ValueError(f"Expected `candidates` list in {path}")
    return data


def write_asset_manifest(project_path: Path, data: dict[str, object]) -> Path:
    path = project_path / MANIFEST_FILE
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def list_asset_candidates(project_path: Path, status: str | None = None) -> list[dict[str, object]]:
    candidates = list(load_asset_manifest(project_path).get("candidates", []))
    if status:
        candidates = [
            candidate for candidate in candidates if str(candidate.get("status", "")) == status
        ]
    return candidates


def import_asset(
    project_path: Path,
    source_path: Path,
    asset_type: str,
    *,
    candidate_id: str | None = None,
    provider: str = "",
    request_id: str = "",
    notes: str = "",
    entity: str | None = None,
    shot: int | None = None,
    line: int | None = None,
    cue: str | None = None,
    label: str = "rough_cut",
    version: int = 1,
    ext: str | None = None,
    force: bool = False,
) -> AssetImportResult:
    if asset_type not in ASSET_TYPES:
        valid = ", ".join(ASSET_TYPES)
        raise ValueError(f"Unknown asset type `{asset_type}`. Valid types: {valid}")
    if not source_path.exists():
        raise FileNotFoundError(f"Asset source does not exist: {source_path}")

    extension = ext or source_path.suffix.removeprefix(".")
    destination = asset_path(
        project_path,
        asset_type,
        project_slug=project_path.name,
        entity=entity,
        shot=shot,
        line=line,
        cue=cue,
        label=label,
        version=version,
        ext=extension or None,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force and source_path.resolve() != destination.resolve():
        raise FileExistsError(f"Asset destination already exists: {destination}")
    if source_path.resolve() != destination.resolve():
        shutil.copy2(source_path, destination)

    manifest = load_asset_manifest(project_path)
    candidates = list(manifest.get("candidates", []))
    safe_candidate_id = candidate_id or _default_candidate_id(
        asset_type=asset_type,
        entity=entity,
        shot=shot,
        line=line,
        cue=cue,
        version=version,
    )
    if any(candidate.get("candidate_id") == safe_candidate_id for candidate in candidates):
        if not force:
            raise ValueError(f"Asset candidate already exists: {safe_candidate_id}")
        candidates = [
            candidate
            for candidate in candidates
            if candidate.get("candidate_id") != safe_candidate_id
        ]

    candidates.append(
        {
            "candidate_id": safe_candidate_id,
            "asset_type": asset_type,
            "path": _project_relative(project_path, destination),
            "source_path": str(source_path),
            "provider": provider,
            "request_id": request_id,
            "status": "generated",
            "notes": notes,
            "entity": entity or "",
            "shot_number": shot if shot is not None else "",
            "line_id": line if line is not None else "",
            "cue_id": cue or "",
            "created_utc": _utc_stamp(),
        }
    )
    manifest["candidates"] = candidates
    manifest_path = write_asset_manifest(project_path, manifest)
    return AssetImportResult(
        candidate_id=safe_candidate_id,
        destination=destination,
        manifest_path=manifest_path,
    )


def set_asset_status(
    project_path: Path,
    candidate_id: str,
    *,
    status: str = "selected",
    notes: str = "",
) -> AssetSelectionResult:
    if status not in ARTIFACT_STATUSES:
        valid = ", ".join(ARTIFACT_STATUSES)
        raise ValueError(f"Invalid asset status `{status}`. Valid statuses: {valid}")

    manifest = load_asset_manifest(project_path)
    candidates = list(manifest.get("candidates", []))
    candidate = None
    for item in candidates:
        if item.get("candidate_id") == candidate_id:
            candidate = item
            break
    if candidate is None:
        raise ValueError(f"Unknown asset candidate: {candidate_id}")

    candidate["status"] = status
    if notes:
        existing = str(candidate.get("notes", "")).strip()
        candidate["notes"] = f"{existing}\n{notes}".strip() if existing else notes
    candidate["updated_utc"] = _utc_stamp()
    manifest["candidates"] = candidates
    manifest_path = write_asset_manifest(project_path, manifest)

    updated_files: list[Path] = [manifest_path]
    if status == "selected":
        updated_files.extend(_apply_selection(project_path, candidate))

    return AssetSelectionResult(
        candidate_id=candidate_id,
        status=status,
        updated_files=tuple(dict.fromkeys(updated_files)),
    )


def missing_media(project_path: Path) -> list[MissingMedia]:
    missing: list[MissingMedia] = []
    seen: set[tuple[str, str, str]] = set()
    for source, field, relative in _referenced_media(project_path):
        if not relative:
            continue
        target = project_path / relative
        key = (source, field, relative)
        if key in seen:
            continue
        seen.add(key)
        if not target.exists():
            missing.append(MissingMedia(source=source, field=field, path=target))
    return missing


def _apply_selection(project_path: Path, candidate: dict[str, object]) -> list[Path]:
    asset_type = str(candidate.get("asset_type", ""))
    relative_path = str(candidate.get("path", ""))
    updated: list[Path] = []

    if asset_type == "storyboard":
        path = project_path / "image_prompts.csv"
        if _update_csv(
            path,
            lambda row: _matches_candidate_or_shot(row, candidate),
            lambda row: _set(row, status="selected", selected_asset=relative_path),
        ):
            updated.append(path)
    elif asset_type == "video_clip":
        path = project_path / "video_prompts.csv"
        if _update_csv(
            path,
            lambda row: row.get("shot_number") == str(candidate.get("shot_number", "")),
            lambda row: _set(row, status="selected", selected_clip=relative_path),
        ):
            updated.append(path)
        edit_plan = _update_edit_plan_clip(project_path, candidate, relative_path)
        if edit_plan is not None:
            updated.append(edit_plan)
    elif asset_type == "voice":
        path = project_path / "voice_lines.csv"
        if _update_csv(
            path,
            lambda row: row.get("line_id") == str(candidate.get("line_id", "")),
            lambda row: _set(row, status="selected", audio_asset=relative_path),
        ):
            updated.append(path)
    elif asset_type in ("sfx", "music"):
        path = project_path / "sound_plan.csv"
        if _update_csv(
            path,
            lambda row: row.get("cue_id") == str(candidate.get("cue_id", "")),
            lambda row: _set(row, status="selected", audio_asset=relative_path),
        ):
            updated.append(path)
    elif asset_type == "reference":
        path = _update_character_reference(project_path, candidate, relative_path)
        if path is not None:
            updated.append(path)

    return updated


def _referenced_media(project_path: Path) -> list[tuple[str, str, str]]:
    references: list[tuple[str, str, str]] = []
    for filename, fields in (
        ("image_prompts.csv", ("selected_asset",)),
        ("video_prompts.csv", ("source_image", "selected_clip")),
        ("voice_lines.csv", ("audio_asset",)),
        ("sound_plan.csv", ("audio_asset",)),
    ):
        for row in _read_csv(project_path / filename):
            label = _row_label(row)
            for field in fields:
                value = row.get(field, "")
                if value:
                    references.append((f"{filename}:{label}", field, value))

    edit_plan = project_path / "edit_plan.json"
    if edit_plan.exists():
        try:
            data = json.loads(edit_plan.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        if isinstance(data, dict):
            for clip in data.get("clips", []):
                if isinstance(clip, dict) and clip.get("video_asset"):
                    references.append(
                        (
                            f"edit_plan.json:shot_{clip.get('shot_number', '')}",
                            "video_asset",
                            str(clip["video_asset"]),
                        )
                    )
            audio = data.get("audio", {})
            if isinstance(audio, dict):
                for group, items in audio.items():
                    if not isinstance(items, list):
                        continue
                    for index, item in enumerate(items, start=1):
                        if isinstance(item, dict) and item.get("asset"):
                            references.append(
                                (f"edit_plan.json:{group}_{index}", "asset", str(item["asset"]))
                            )

    for candidate in list_asset_candidates(project_path):
        path = str(candidate.get("path", ""))
        if path:
            references.append(
                (
                    f"asset_manifest.json:{candidate.get('candidate_id', '')}",
                    "path",
                    path,
                )
            )
    return references


def _update_csv(
    path: Path,
    matcher: Callable[[dict[str, str]], bool],
    updater: Callable[[dict[str, str]], None],
) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]

    changed = False
    for row in rows:
        if matcher(row):
            updater(row)
            changed = True

    if changed:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    return changed


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(file)
            if any((value or "").strip() for value in row.values())
        ]


def _set(row: dict[str, str], **values: str) -> None:
    for key, value in values.items():
        row[key] = value


def _matches_candidate_or_shot(row: dict[str, str], candidate: dict[str, object]) -> bool:
    if row.get("candidate_id") == str(candidate.get("candidate_id", "")):
        return True
    return row.get("shot_number") == str(candidate.get("shot_number", "")) and not row.get(
        "selected_asset"
    )


def _update_edit_plan_clip(
    project_path: Path,
    candidate: dict[str, object],
    relative_path: str,
) -> Path | None:
    path = project_path / "edit_plan.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    clips = data.get("clips")
    if not isinstance(clips, list):
        return None
    changed = False
    for clip in clips:
        if not isinstance(clip, dict):
            continue
        if str(clip.get("shot_number", "")) == str(candidate.get("shot_number", "")):
            clip["video_asset"] = relative_path
            changed = True
    if not changed:
        return None
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _update_character_reference(
    project_path: Path,
    candidate: dict[str, object],
    relative_path: str,
) -> Path | None:
    entity = str(candidate.get("entity", ""))
    if not entity:
        return None
    path = project_path / "characters.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    characters = data.get("characters")
    if not isinstance(characters, list):
        return None
    changed = False
    for character in characters:
        if not isinstance(character, dict):
            continue
        identifiers = {
            str(character.get("id", "")).strip(),
            _safe_slug(str(character.get("id", ""))),
            _safe_slug(str(character.get("name", ""))),
        }
        if entity not in identifiers and _safe_slug(entity) not in identifiers:
            continue
        references = character.setdefault("reference_assets", [])
        if isinstance(references, list) and relative_path not in references:
            references.append(relative_path)
            changed = True
    if not changed:
        return None
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _project_relative(project_path: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_path.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"Asset path must stay inside project: {path}") from exc


def _default_candidate_id(
    *,
    asset_type: str,
    entity: str | None,
    shot: int | None,
    line: int | None,
    cue: str | None,
    version: int,
) -> str:
    parts = [asset_type]
    if entity:
        parts.append(slugify(entity))
    if shot is not None:
        parts.append(f"shot-{shot:03d}")
    if line is not None:
        parts.append(f"line-{line:03d}")
    if cue:
        parts.append(slugify(cue))
    parts.append(f"v{version:03d}")
    return "_".join(parts)


def _empty_manifest() -> dict[str, object]:
    return {"version": MANIFEST_VERSION, "candidates": []}


def _row_label(row: dict[str, str]) -> str:
    for key in ("candidate_id", "line_id", "cue_id", "shot_number"):
        if row.get(key):
            return f"{key}_{row[key]}"
    return "row"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_slug(value: str) -> str:
    try:
        return slugify(value)
    except ValueError:
        return ""
