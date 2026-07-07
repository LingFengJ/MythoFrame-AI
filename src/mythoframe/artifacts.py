"""Apply collected model outputs to canonical project artifacts."""

from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from mythoframe.project import validate_project
from mythoframe.schemas import CSV_REQUIRED_HEADERS, STAGE_NAMES


@dataclass(frozen=True)
class ApplyResult:
    output_path: Path
    written_files: tuple[Path, ...]
    backup_dir: Path | None


STAGE_TARGETS = {
    "adaptation": ("adaptation.md",),
    "script": ("script.md",),
    "characters": ("characters.json",),
    "shot_table": ("shot_table.csv",),
    "image_prompts": ("image_prompts.csv",),
    "video_prompts": ("video_prompts.csv",),
    "sound_plan": ("voice_lines.csv", "sound_plan.csv"),
    "edit_plan": ("edit_plan.json",),
}


def latest_output(project_path: Path, stage: str) -> Path:
    output_dir = project_path / "outputs" / stage
    candidates = sorted(output_dir.glob("*.md"))
    if not candidates:
        raise FileNotFoundError(f"No collected outputs found for stage `{stage}` in {output_dir}")
    return candidates[-1]


def apply_stage_output(
    project_path: Path,
    stage: str,
    output_path: Path | None = None,
    *,
    keep_invalid: bool = False,
) -> ApplyResult:
    if stage not in STAGE_NAMES:
        valid = ", ".join(STAGE_NAMES)
        raise ValueError(f"Unknown stage `{stage}`. Valid stages: {valid}")

    source = output_path or latest_output(project_path, stage)
    if not source.exists():
        raise FileNotFoundError(f"Output file does not exist: {source}")

    artifacts = _extract_stage_artifacts(stage, source.read_text(encoding="utf-8"))
    backup_dir = _backup_targets(project_path, artifacts.keys())
    written = tuple(project_path / filename for filename in artifacts)

    try:
        for filename, content in artifacts.items():
            (project_path / filename).write_text(content, encoding="utf-8", newline="\n")

        problems = validate_project(project_path)
        if problems and not keep_invalid:
            _restore_backup(project_path, backup_dir)
            details = "\n".join(f"- {problem}" for problem in problems)
            raise ValueError(f"Applied output failed validation and was rolled back:\n{details}")
    except Exception:
        if backup_dir is not None:
            _restore_backup(project_path, backup_dir)
        raise

    return ApplyResult(output_path=source, written_files=written, backup_dir=backup_dir)


def _extract_stage_artifacts(stage: str, text: str) -> dict[str, str]:
    if stage in ("adaptation", "script"):
        return {STAGE_TARGETS[stage][0]: _extract_markdown(text)}
    if stage in ("characters", "edit_plan"):
        return {STAGE_TARGETS[stage][0]: _extract_json(text)}
    if stage in ("shot_table", "image_prompts", "video_prompts"):
        filename = STAGE_TARGETS[stage][0]
        return {filename: _extract_csv(text, CSV_REQUIRED_HEADERS[filename])}
    if stage == "sound_plan":
        return {
            "voice_lines.csv": _extract_csv(text, CSV_REQUIRED_HEADERS["voice_lines.csv"]),
            "sound_plan.csv": _extract_csv(text, CSV_REQUIRED_HEADERS["sound_plan.csv"]),
        }
    raise ValueError(f"Unsupported stage: {stage}")


def _extract_markdown(text: str) -> str:
    for language, body in _fenced_blocks(text):
        if language in ("markdown", "md", ""):
            return body.strip() + "\n"
    return text.strip() + "\n"


def _extract_json(text: str) -> str:
    candidates = [body for language, body in _fenced_blocks(text) if language == "json"]
    candidates.append(text)

    for candidate in candidates:
        snippet = _json_snippet(candidate)
        if snippet is None:
            continue
        try:
            value = json.loads(snippet)
        except json.JSONDecodeError:
            continue
        return json.dumps(value, ensure_ascii=False, indent=2) + "\n"

    raise ValueError("Could not find valid JSON in model output.")


def _extract_csv(text: str, expected_headers: tuple[str, ...]) -> str:
    header = ",".join(expected_headers)
    candidates = [
        body
        for language, body in _fenced_blocks(text)
        if language in ("csv", "text", "")
    ]
    candidates.append(text)

    for candidate in candidates:
        csv_text = _csv_from_text(candidate, header)
        if csv_text is None:
            continue
        normalized = _normalize_csv(csv_text)
        if normalized.splitlines()[0] == header:
            return normalized

    raise ValueError(f"Could not find CSV block with header: {header}")


def _fenced_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"```([A-Za-z0-9_-]*)\s*\n(.*?)```", re.DOTALL)
    return [
        (match.group(1).strip().lower(), match.group(2).strip())
        for match in pattern.finditer(text)
    ]


def _json_snippet(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped[0] in "[{":
        return stripped
    starts = [index for index in (stripped.find("{"), stripped.find("[")) if index >= 0]
    if not starts:
        return None
    start = min(starts)
    end = max(stripped.rfind("}"), stripped.rfind("]"))
    if end <= start:
        return None
    return stripped[start : end + 1]


def _csv_from_text(text: str, header: str) -> str | None:
    lines = [line.rstrip() for line in text.strip().splitlines()]
    for start, line in enumerate(lines):
        if line.strip() != header:
            continue
        collected: list[str] = []
        for line in lines[start:]:
            if not line.strip() and collected:
                break
            if line.strip().startswith("```"):
                break
            collected.append(line)
        return "\n".join(collected).strip() + "\n"
    return None


def _normalize_csv(text: str) -> str:
    input_buffer = StringIO(text.strip())
    output_buffer = StringIO()
    writer = csv.writer(output_buffer, lineterminator="\n")
    for row in csv.reader(input_buffer):
        writer.writerow(row)
    return output_buffer.getvalue()


def _backup_targets(project_path: Path, filenames: object) -> Path | None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_dir = project_path / "outputs" / "applied_backups" / stamp
    copied = False
    for filename in filenames:
        source = project_path / filename
        if not source.exists():
            continue
        target = backup_dir / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied = True
    return backup_dir if copied else None


def _restore_backup(project_path: Path, backup_dir: Path | None) -> None:
    if backup_dir is None or not backup_dir.exists():
        return
    for source in backup_dir.rglob("*"):
        if source.is_file():
            target = project_path / source.relative_to(backup_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
