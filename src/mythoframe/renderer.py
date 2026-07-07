"""Optional local rough-cut rendering helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def render_rough_cut(project_path: Path, output_path: Path | None = None) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is not installed or not on PATH.")

    edit_plan = json.loads((project_path / "edit_plan.json").read_text(encoding="utf-8"))
    clips = edit_plan.get("clips", [])
    if not clips:
        raise ValueError("edit_plan.json has no clips to render.")

    missing = [
        str(project_path / clip["video_asset"])
        for clip in clips
        if not (project_path / clip["video_asset"]).exists()
    ]
    if missing:
        details = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing video assets:\n{details}")

    output = output_path or (project_path / "assets" / "exports" / "rough_cut.mp4")
    output.parent.mkdir(parents=True, exist_ok=True)

    concat_file = output.with_suffix(".concat.txt")
    concat_file.write_text(
        "\n".join(
            f"file '{(project_path / clip['video_asset']).resolve().as_posix()}'"
            for clip in clips
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output),
        ],
        check=True,
    )
    return output
