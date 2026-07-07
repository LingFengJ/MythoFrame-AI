"""Subtitle export helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def export_subtitles(project_path: Path, fmt: str = "srt", output_path: Path | None = None) -> Path:
    fmt = fmt.lower()
    if fmt not in ("srt", "vtt"):
        raise ValueError("Subtitle format must be `srt` or `vtt`.")

    cues = _subtitle_cues(project_path)
    output = output_path or (project_path / "assets" / "exports" / f"subtitles.{fmt}")
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "srt":
        output.write_text(_render_srt(cues), encoding="utf-8", newline="\n")
    else:
        output.write_text(_render_vtt(cues), encoding="utf-8", newline="\n")
    return output


def _subtitle_cues(project_path: Path) -> list[dict[str, object]]:
    edit_plan = project_path / "edit_plan.json"
    if edit_plan.exists():
        data = json.loads(edit_plan.read_text(encoding="utf-8"))
        subtitles = data.get("subtitles", [])
        if subtitles:
            return [
                {
                    "start": str(cue["start"]),
                    "duration": str(cue["duration"]),
                    "text": _cue_text(cue),
                }
                for cue in subtitles
            ]

    return _cues_from_voice_and_shots(project_path)


def _cues_from_voice_and_shots(project_path: Path) -> list[dict[str, object]]:
    shots = _read_csv(project_path / "shot_table.csv")
    voice = _read_csv(project_path / "voice_lines.csv")
    shot_starts: dict[str, tuple[str, str]] = {}
    current = 0.0
    for shot in shots:
        shot_starts[shot["shot_number"]] = (_timestamp(current), shot["duration"])
        current += _duration_seconds(shot["duration"])

    cues: list[dict[str, object]] = []
    for line in voice:
        if not line.get("text"):
            continue
        start, duration = shot_starts.get(line.get("shot_number", ""), ("00:00:00.000", "3s"))
        cues.append({"start": start, "duration": duration, "text": _cue_text(line)})
    return cues


def _cue_text(cue: dict[str, object]) -> str:
    speaker = str(cue.get("speaker", "")).strip()
    text = str(cue.get("text", "")).strip()
    return f"{speaker}: {text}" if speaker else text


def _render_srt(cues: list[dict[str, object]]) -> str:
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        start = _srt_timestamp(str(cue["start"]))
        end = _srt_timestamp(_add_duration(str(cue["start"]), str(cue["duration"])))
        blocks.append(f"{index}\n{start} --> {end}\n{cue['text']}")
    return "\n\n".join(blocks).strip() + "\n"


def _render_vtt(cues: list[dict[str, object]]) -> str:
    blocks = ["WEBVTT"]
    for cue in cues:
        start = str(cue["start"])
        end = _add_duration(start, str(cue["duration"]))
        blocks.append(f"{start} --> {end}\n{cue['text']}")
    return "\n\n".join(blocks).strip() + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(file)
            if any((value or "").strip() for value in row.values())
        ]


def _duration_seconds(duration: str) -> float:
    return float(duration.removesuffix("s"))


def _add_duration(timestamp: str, duration: str) -> str:
    return _timestamp(_timestamp_seconds(timestamp) + _duration_seconds(duration))


def _timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def _timestamp_seconds(timestamp: str) -> float:
    hours, minutes, rest = timestamp.split(":")
    seconds, milliseconds = rest.split(".")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000
    )


def _srt_timestamp(timestamp: str) -> str:
    return timestamp.replace(".", ",")

