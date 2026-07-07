"""Local edit-plan helpers that do not render media."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def build_draft_edit_plan(project_path: Path) -> dict[str, object]:
    shots = _read_csv(project_path / "shot_table.csv")
    video_prompts = {
        row["shot_number"]: row for row in _read_csv(project_path / "video_prompts.csv")
    }
    voice_lines = _read_csv(project_path / "voice_lines.csv")
    sound_cues = _read_csv(project_path / "sound_plan.csv")

    current = 0.0
    clips: list[dict[str, object]] = []
    subtitles: list[dict[str, object]] = []

    for shot in shots:
        shot_number = int(shot["shot_number"])
        duration = _duration_seconds(shot["duration"])
        video_row = video_prompts.get(shot["shot_number"], {})
        video_asset = video_row.get("selected_clip") or video_row.get("source_image") or (
            f"assets/video_clips/shot_{shot_number:03d}_clip_v001.mp4"
        )
        clips.append(
            {
                "shot_number": shot_number,
                "video_asset": video_asset,
                "start": _timestamp(current),
                "duration": shot["duration"],
                "transition_in": "cut",
                "transition_out": "cut",
                "notes": shot.get("visual_description", ""),
            }
        )
        for line in voice_lines:
            if line.get("shot_number") == shot["shot_number"] and line.get("text"):
                subtitles.append(
                    {
                        "shot_number": shot_number,
                        "start": _timestamp(current),
                        "duration": shot["duration"],
                        "speaker": line.get("speaker", ""),
                        "text": line.get("text", ""),
                    }
                )
        current += duration

    return {
        "timeline": {
            "aspect_ratio": "16:9",
            "runtime": f"{current:.1f}s",
            "frame_rate": "24fps",
        },
        "clips": clips,
        "audio": {
            "dialogue": _audio_items(voice_lines, kind="dialogue"),
            "narration": _audio_items(
                [line for line in voice_lines if line.get("speaker", "").lower() == "narrator"],
                kind="narration",
            ),
            "music": _sound_items(sound_cues, "music"),
            "sound_effects": _sound_items(sound_cues, "sfx"),
        },
        "subtitles": subtitles,
        "review_gates": ["pacing", "continuity", "audio balance", "caption timing"],
        "automation": {
            "rough_cut": "planned",
            "final_review_required": True,
        },
    }


def write_draft_edit_plan(project_path: Path) -> Path:
    target = project_path / "edit_plan.json"
    target.write_text(
        json.dumps(build_draft_edit_plan(project_path), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def export_edit_manifest(project_path: Path, output_path: Path | None = None) -> Path:
    edit_plan = json.loads((project_path / "edit_plan.json").read_text(encoding="utf-8"))
    output = output_path or (project_path / "assets" / "exports" / "edit_manifest.txt")
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = ["# MythoFrame Edit Manifest", ""]
    for clip in edit_plan.get("clips", []):
        lines.append(
            f"{clip.get('start')} | {clip.get('duration')} | "
            f"shot {clip.get('shot_number')} | {clip.get('video_asset')}"
        )
    lines.append("")
    lines.append("# Audio")
    audio = edit_plan.get("audio", {})
    if isinstance(audio, dict):
        for group, items in audio.items():
            for item in items:
                lines.append(f"{group}: {item}")
    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8", newline="\n")
    return output


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
    if duration.endswith("s"):
        duration = duration[:-1]
    return float(duration)


def _timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def _audio_items(rows: list[dict[str, str]], kind: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for row in rows:
        asset = row.get("audio_asset")
        if not asset:
            continue
        items.append(
            {
                "kind": kind,
                "shot_number": row.get("shot_number", ""),
                "asset": asset,
                "text": row.get("text", ""),
            }
        )
    return items


def _sound_items(rows: list[dict[str, str]], cue_type: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for row in rows:
        if row.get("cue_type") != cue_type:
            continue
        items.append(
            {
                "shot_number": row.get("shot_number", ""),
                "asset": row.get("audio_asset", ""),
                "description": row.get("description", ""),
                "timing": row.get("timing", ""),
            }
        )
    return items
