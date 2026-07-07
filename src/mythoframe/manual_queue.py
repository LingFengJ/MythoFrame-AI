"""File-based generation queue for manual and Codex-assisted workflows."""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mythoframe.schemas import OUTPUT_MARKER


@dataclass(frozen=True)
class RequestRecord:
    request_id: str
    stage: str
    request_path: Path
    response_path: Path
    mode: str
    target_model: str = ""
    target_site: str = ""


def create_request(
    project_path: Path,
    stage: str,
    prompt: str,
    mode: str = "manual_file",
    metadata: dict[str, str] | None = None,
    acceptance_checklist: list[str] | None = None,
) -> RequestRecord:
    request_id = _request_id(stage)
    pending = project_path / "requests" / "pending"
    pending.mkdir(parents=True, exist_ok=True)

    request_path = pending / f"{request_id}.request.md"
    response_path = pending / f"{request_id}.response.md"

    request_path.write_text(
        _request_text(
            request_id=request_id,
            stage=stage,
            prompt=prompt,
            mode=mode,
            metadata=metadata or {},
            acceptance_checklist=acceptance_checklist or [],
        ),
        encoding="utf-8",
        newline="\n",
    )
    response_path.write_text(
        _response_text(request_id=request_id, stage=stage, mode=mode),
        encoding="utf-8",
        newline="\n",
    )
    return RequestRecord(
        request_id=request_id,
        stage=stage,
        request_path=request_path,
        response_path=response_path,
        mode=mode,
        target_model=(metadata or {}).get("target_model", ""),
        target_site=(metadata or {}).get("target_site", ""),
    )


def list_pending(project_path: Path) -> list[RequestRecord]:
    pending = project_path / "requests" / "pending"
    if not pending.exists():
        return []

    records: list[RequestRecord] = []
    for request_path in sorted(pending.glob("*.request.md")):
        request_id = request_path.name.removesuffix(".request.md")
        response_path = pending / f"{request_id}.response.md"
        stage = _stage_from_request_id(request_id)
        metadata = _request_metadata_from_file(request_path)
        records.append(
            RequestRecord(
                request_id=request_id,
                stage=stage,
                request_path=request_path,
                response_path=response_path,
                mode=metadata.get("mode", "unknown"),
                target_model=metadata.get("target_model", ""),
                target_site=metadata.get("target_site", ""),
            )
        )
    return records


def list_completed(project_path: Path) -> list[RequestRecord]:
    completed = project_path / "requests" / "completed"
    if not completed.exists():
        return []

    records: list[RequestRecord] = []
    for request_path in sorted(completed.glob("*.request.md")):
        request_id = request_path.name.removesuffix(".request.md")
        response_path = completed / f"{request_id}.response.md"
        stage = _stage_from_request_id(request_id)
        metadata = _request_metadata_from_file(request_path)
        records.append(
            RequestRecord(
                request_id=request_id,
                stage=stage,
                request_path=request_path,
                response_path=response_path,
                mode=metadata.get("mode", "unknown"),
                target_model=metadata.get("target_model", ""),
                target_site=metadata.get("target_site", ""),
            )
        )
    return records


def response_body(response_path: Path) -> str:
    if not response_path.exists():
        return ""
    text = response_path.read_text(encoding="utf-8")
    if OUTPUT_MARKER not in text:
        return text.strip()
    return text.split(OUTPUT_MARKER, 1)[1].strip()


def is_ready(response_path: Path) -> bool:
    return bool(response_body(response_path))


def wait_for_response(
    response_path: Path,
    poll_seconds: float = 10.0,
    timeout_seconds: float | None = None,
) -> str:
    started = time.monotonic()
    while True:
        body = response_body(response_path)
        if body:
            return body
        if timeout_seconds is not None and time.monotonic() - started >= timeout_seconds:
            raise TimeoutError(f"Timed out waiting for response: {response_path}")
        time.sleep(poll_seconds)


def collect_response(project_path: Path, request_id: str) -> Path:
    pending = project_path / "requests" / "pending"
    completed = project_path / "requests" / "completed"
    completed.mkdir(parents=True, exist_ok=True)

    request_path = pending / f"{request_id}.request.md"
    response_path = pending / f"{request_id}.response.md"
    if not response_path.exists():
        raise FileNotFoundError(f"Missing response file: {response_path}")

    body = response_body(response_path)
    if not body:
        raise ValueError(f"Response is still empty: {response_path}")

    stage = _stage_from_request_id(request_id)
    output_dir = project_path / "outputs" / stage
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{request_id}.md"
    output_path.write_text(body + "\n", encoding="utf-8", newline="\n")

    if request_path.exists():
        shutil.move(str(request_path), str(completed / request_path.name))
    shutil.move(str(response_path), str(completed / response_path.name))

    return output_path


def _request_id(stage: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    safe_stage = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in stage)
    return f"{stamp}_{safe_stage}"


def _stage_from_request_id(request_id: str) -> str:
    parts = request_id.split("_", 1)
    if len(parts) == 1:
        return "misc"
    return parts[1]


def _request_metadata_from_file(request_path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    try:
        lines = request_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return metadata
    for line in lines:
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        normalized = key.strip().lower().replace(" ", "_")
        metadata[normalized] = value.strip()
    return metadata


def _request_text(
    request_id: str,
    stage: str,
    prompt: str,
    mode: str,
    metadata: dict[str, str],
    acceptance_checklist: list[str],
) -> str:
    mode_note = {
        "manual_file": (
            "Manual mode: paste this prompt into the model web app yourself, then "
            "paste the result into the matching response file."
        ),
        "codex_web": (
            "Codex-assisted web mode: ask Codex to open the model web app through "
            "browser use where possible, computer use where necessary, then paste "
            "the model output into the response file."
        ),
    }.get(mode, "Generation request.")

    metadata_lines = [
        f"- Request Id: {request_id}",
        f"- Stage: {stage}",
        f"- Mode: {mode}",
    ]
    for key, value in metadata.items():
        if value:
            label = key.replace("_", " ").title()
            metadata_lines.append(f"- {label}: {value}")

    checklist = ""
    if acceptance_checklist:
        checklist = "\n## Acceptance Checklist\n\n" + "\n".join(
            f"- [ ] {item}" for item in acceptance_checklist
        )
        checklist += "\n"

    return (
        f"# MythoFrame Request: {request_id}\n\n"
        "## Request Metadata\n\n"
        + "\n".join(metadata_lines)
        + "\n\n"
        f"{mode_note}\n\n"
        f"{checklist}\n"
        "## Prompt\n\n"
        f"{prompt.strip()}\n"
    )


def _response_text(request_id: str, stage: str, mode: str) -> str:
    return (
        f"# MythoFrame Response: {request_id}\n\n"
        f"- Stage: {stage}\n"
        f"- Mode: {mode}\n\n"
        "Paste the model output below the marker. Leave everything above it intact.\n\n"
        f"{OUTPUT_MARKER}\n"
    )
