"""Stage prompt rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from mythoframe.schemas import STAGE_NAMES


@dataclass(frozen=True)
class StageSpec:
    name: str
    title: str
    template_file: str
    output_artifacts: tuple[str, ...]
    acceptance_checklist: tuple[str, ...]


STAGE_SPECS: dict[str, StageSpec] = {
    "adaptation": StageSpec(
        name="adaptation",
        title="Story Adaptation",
        template_file="adaptation.md",
        output_artifacts=("adaptation.md",),
        acceptance_checklist=(
            "Keeps source rights and upload risks explicit.",
            "Compresses the source into one 60-90 second cinematic scene.",
            "Identifies character, conflict, emotional arc, and visual hook.",
        ),
    ),
    "script": StageSpec(
        name="script",
        title="Short Script",
        template_file="script.md",
        output_artifacts=("script.md",),
        acceptance_checklist=(
            "Fits a 60-90 second horizontal short.",
            "Includes dialogue, narration, emotion, and visual intent.",
            "Avoids trying to cover an entire book or arc.",
        ),
    ),
    "characters": StageSpec(
        name="characters",
        title="Character Bible",
        template_file="characters.md",
        output_artifacts=("characters.json",),
        acceptance_checklist=(
            "Outputs valid JSON only.",
            "Defines reusable visual identity for each recurring character.",
            "Includes consistency and negative drift notes.",
        ),
    ),
    "shot_table": StageSpec(
        name="shot_table",
        title="Shot Table",
        template_file="shot_table.md",
        output_artifacts=("shot_table.csv",),
        acceptance_checklist=(
            "Outputs CSV with the exact requested header.",
            "Keeps each shot around three seconds or less.",
            "Uses one main action or emotion per shot.",
        ),
    ),
    "image_prompts": StageSpec(
        name="image_prompts",
        title="Image Prompts",
        template_file="image_prompts.md",
        output_artifacts=("image_prompts.csv",),
        acceptance_checklist=(
            "Outputs CSV with the exact requested header.",
            "Prompts include subject, action, environment, composition, light, style, and quality.",
            "Preserves character consistency through references or repeated identity traits.",
        ),
    ),
    "video_prompts": StageSpec(
        name="video_prompts",
        title="Video Prompts",
        template_file="video_prompts.md",
        output_artifacts=("video_prompts.csv",),
        acceptance_checklist=(
            "Outputs CSV with the exact requested header.",
            "Each prompt describes motion, camera movement, emotion change, and environment dynamics.",
            "Avoids complex multi-action instructions in one clip.",
        ),
    ),
    "sound_plan": StageSpec(
        name="sound_plan",
        title="Sound Plan",
        template_file="sound_plan.md",
        output_artifacts=("voice_lines.csv", "sound_plan.csv"),
        acceptance_checklist=(
            "Separates dialogue/narration from music, ambience, and SFX.",
            "Gives timing notes that match the shot table.",
            "Keeps sound cues concrete enough for generation or manual editing.",
        ),
    ),
    "edit_plan": StageSpec(
        name="edit_plan",
        title="Edit Plan",
        template_file="edit_plan.md",
        output_artifacts=("edit_plan.json",),
        acceptance_checklist=(
            "Outputs valid JSON only.",
            "Represents an edit decision list, not a rendered video.",
            "Keeps human review gates for pacing, continuity, and audio balance.",
        ),
    ),
}


def list_stage_specs() -> list[StageSpec]:
    return [STAGE_SPECS[name] for name in STAGE_NAMES]


def get_stage_spec(stage: str) -> StageSpec:
    try:
        return STAGE_SPECS[stage]
    except KeyError as exc:
        valid = ", ".join(STAGE_NAMES)
        raise ValueError(f"Unknown stage `{stage}`. Valid stages: {valid}") from exc


def render_stage_prompt(
    root: Path,
    project_path: Path,
    stage: str,
    source_file: Path | None = None,
) -> str:
    spec = get_stage_spec(stage)
    template_path = root / "prompts" / "stages" / spec.template_file
    if not template_path.exists():
        raise FileNotFoundError(f"Missing prompt template: {template_path}")

    source_path = _resolve_source_file(root, project_path, source_file)
    context = _context(project_path, source_path)
    template = template_path.read_text(encoding="utf-8")
    return _render(template, context).strip() + "\n"


def _resolve_source_file(root: Path, project_path: Path, source_file: Path | None) -> Path:
    if source_file is None:
        return project_path / "source_brief.md"
    if source_file.is_absolute():
        return source_file
    return root / source_file


def _context(project_path: Path, source_path: Path) -> dict[str, str]:
    files = {
        "project_bible": project_path / "project_bible.json",
        "source_brief": source_path,
        "adaptation": project_path / "adaptation.md",
        "script": project_path / "script.md",
        "characters": project_path / "characters.json",
        "shot_table": project_path / "shot_table.csv",
        "image_prompts": project_path / "image_prompts.csv",
        "video_prompts": project_path / "video_prompts.csv",
        "voice_lines": project_path / "voice_lines.csv",
        "sound_plan": project_path / "sound_plan.csv",
        "edit_plan": project_path / "edit_plan.json",
    }
    return {name: _read(path) for name, path in files.items()}


def _read(path: Path) -> str:
    if not path.exists():
        return f"[missing: {path}]"
    text = path.read_text(encoding="utf-8").strip()
    return text if text else f"[empty: {path}]"


def _render(template: str, context: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return context.get(key, f"[unknown template variable: {key}]")

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace, template)

