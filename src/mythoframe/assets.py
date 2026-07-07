"""Asset naming conventions."""

from __future__ import annotations

from pathlib import Path

from mythoframe.project import slugify


ASSET_TYPES = (
    "reference",
    "storyboard",
    "video_clip",
    "voice",
    "sfx",
    "music",
    "export",
)


def asset_path(
    project_path: Path,
    asset_type: str,
    *,
    project_slug: str | None = None,
    entity: str | None = None,
    shot: int | None = None,
    line: int | None = None,
    cue: str | None = None,
    label: str = "rough_cut",
    version: int = 1,
    ext: str | None = None,
) -> Path:
    if asset_type == "reference":
        _require(entity, "entity")
        return project_path / "assets" / "references" / (
            f"{slugify(entity or '')}_ref_v{version:03d}.{ext or 'png'}"
        )
    if asset_type == "storyboard":
        _require(shot, "shot")
        return project_path / "assets" / "storyboards" / (
            f"shot_{shot:03d}_img_v{version:03d}.{ext or 'png'}"
        )
    if asset_type == "video_clip":
        _require(shot, "shot")
        return project_path / "assets" / "video_clips" / (
            f"shot_{shot:03d}_clip_v{version:03d}.{ext or 'mp4'}"
        )
    if asset_type == "voice":
        _require(shot, "shot")
        _require(line, "line")
        return project_path / "assets" / "audio" / "voice" / (
            f"shot_{shot:03d}_line_{line:03d}_v{version:03d}.{ext or 'wav'}"
        )
    if asset_type == "sfx":
        _require(shot, "shot")
        _require(cue, "cue")
        return project_path / "assets" / "audio" / "sfx" / (
            f"shot_{shot:03d}_{slugify(cue or '')}_v{version:03d}.{ext or 'wav'}"
        )
    if asset_type == "music":
        _require(cue, "cue")
        return project_path / "assets" / "audio" / "music" / (
            f"{slugify(cue or '')}_v{version:03d}.{ext or 'wav'}"
        )
    if asset_type == "export":
        _require(project_slug, "project_slug")
        return project_path / "assets" / "exports" / (
            f"{slugify(project_slug or '')}_{slugify(label)}_v{version:03d}.{ext or 'mp4'}"
        )

    valid = ", ".join(ASSET_TYPES)
    raise ValueError(f"Unknown asset type `{asset_type}`. Valid types: {valid}")


def _require(value: object, name: str) -> None:
    if value is None or value == "":
        raise ValueError(f"`{name}` is required for this asset type")
