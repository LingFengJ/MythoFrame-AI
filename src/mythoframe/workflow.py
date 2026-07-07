"""Workflow status helpers."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from mythoframe.manual_queue import is_ready, list_pending
from mythoframe.schemas import STAGE_NAMES


@dataclass(frozen=True)
class StageStatus:
    stage: str
    status: str
    detail: str


STAGE_ARTIFACTS = {
    "adaptation": ("adaptation.md",),
    "script": ("script.md",),
    "characters": ("characters.json",),
    "shot_table": ("shot_table.csv",),
    "image_prompts": ("image_prompts.csv",),
    "video_prompts": ("video_prompts.csv",),
    "sound_plan": ("voice_lines.csv", "sound_plan.csv"),
    "edit_plan": ("edit_plan.json",),
}


def stage_statuses(project_path: Path) -> list[StageStatus]:
    statuses: list[StageStatus] = []
    for stage in STAGE_NAMES:
        artifacts = STAGE_ARTIFACTS[stage]
        artifact_statuses = [_artifact_status(project_path / artifact) for artifact in artifacts]
        if any(status == "missing" for status, _detail in artifact_statuses):
            status = "missing"
        elif all(status == "ready" for status, _detail in artifact_statuses):
            status = "ready"
        else:
            status = "draft"
        detail = "; ".join(f"{artifact}: {detail}" for artifact, (_status, detail) in zip(artifacts, artifact_statuses))
        statuses.append(StageStatus(stage=stage, status=status, detail=detail))
    return statuses


def next_stage(project_path: Path) -> StageStatus | None:
    for status in stage_statuses(project_path):
        if status.status != "ready":
            return status
    return None


def pending_request_summary(project_path: Path) -> list[str]:
    summaries: list[str] = []
    for record in list_pending(project_path):
        state = "ready" if is_ready(record.response_path) else "waiting"
        summaries.append(f"{state}: {record.request_id}")
    return summaries


def latest_collected_outputs(project_path: Path) -> dict[str, Path]:
    outputs: dict[str, Path] = {}
    for stage in STAGE_NAMES:
        stage_dir = project_path / "outputs" / stage
        candidates = sorted(stage_dir.glob("*.md")) if stage_dir.exists() else []
        if candidates:
            outputs[stage] = candidates[-1]
    return outputs


def _artifact_status(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "missing", "missing"
    if path.suffix == ".csv":
        count = _csv_row_count(path)
        if count == 0:
            return "draft", "headers only"
        return "ready", f"{count} data row(s)"
    if path.suffix == ".json":
        return _json_status(path)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return "draft", "empty"
    if "To be generated" in text or "to_be_determined" in text:
        return "draft", "template content"
    return "ready", "content present"


def _csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as file:
        return sum(1 for row in csv.DictReader(file) if any((value or "").strip() for value in row.values()))


def _json_status(path: Path) -> tuple[str, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "draft", "invalid json"

    if path.name == "characters.json":
        count = len(value.get("characters", [])) if isinstance(value, dict) else 0
        if count == 0:
            return "draft", "no characters"
        return "ready", f"{count} character(s)"

    if path.name == "edit_plan.json":
        count = len(value.get("clips", [])) if isinstance(value, dict) else 0
        if count == 0:
            return "draft", "no edit clips"
        return "ready", f"{count} edit clip(s)"

    return "ready", "json present"
