"""Inspect and mechanically repair collected model outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mythoframe.artifacts import STAGE_TARGETS, _extract_stage_artifacts, latest_output
from mythoframe.project import validate_project
from mythoframe.schemas import STAGE_NAMES


@dataclass(frozen=True)
class OutputInspection:
    output_path: Path
    stage: str
    targets: tuple[str, ...]
    parse_ok: bool
    messages: tuple[str, ...]


def inspect_stage_output(
    project_path: Path,
    stage: str,
    output_path: Path | None = None,
) -> OutputInspection:
    source = output_path or latest_output(project_path, stage)
    messages: list[str] = []
    try:
        artifacts = _extract_stage_artifacts(stage, source.read_text(encoding="utf-8"))
    except Exception as exc:
        return OutputInspection(
            output_path=source,
            stage=stage,
            targets=STAGE_TARGETS.get(stage, ()),
            parse_ok=False,
            messages=(str(exc),),
        )

    messages.append(f"Parsed artifacts: {', '.join(artifacts)}")
    messages.extend(_temporary_validation_messages(project_path, artifacts))
    return OutputInspection(
        output_path=source,
        stage=stage,
        targets=tuple(artifacts),
        parse_ok=True,
        messages=tuple(messages),
    )


def repair_stage_output(
    project_path: Path,
    stage: str,
    output_path: Path | None = None,
) -> Path:
    if stage not in STAGE_NAMES:
        valid = ", ".join(STAGE_NAMES)
        raise ValueError(f"Unknown stage `{stage}`. Valid stages: {valid}")

    source = output_path or latest_output(project_path, stage)
    artifacts = _extract_stage_artifacts(stage, source.read_text(encoding="utf-8"))
    repaired = source.with_name(f"{source.stem}.repaired.md")

    blocks = []
    for filename, content in artifacts.items():
        language = "json" if filename.endswith(".json") else "csv" if filename.endswith(".csv") else "markdown"
        blocks.append(f"## {filename}\n\n```{language}\n{content.strip()}\n```")
    repaired.write_text("\n\n".join(blocks).strip() + "\n", encoding="utf-8", newline="\n")
    return repaired


def _temporary_validation_messages(project_path: Path, artifacts: dict[str, str]) -> list[str]:
    # Do not mutate the project here. Inspect only tells whether parsing worked;
    # full validation still happens during apply-output.
    existing_missing = [
        filename for filename in artifacts if not (project_path / filename).exists()
    ]
    if existing_missing:
        return [f"Would create new artifact(s): {', '.join(existing_missing)}"]
    problems = validate_project(project_path)
    if problems:
        return ["Current project validation already has issues before applying output."]
    return ["Current project validates before applying output."]
