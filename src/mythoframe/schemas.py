"""Shared schema names and filesystem conventions."""

from __future__ import annotations

OUTPUT_MARKER = "<!-- MODEL_OUTPUT_BELOW -->"

PROJECT_FILES = (
    "project_bible.json",
    "characters.json",
    "script.md",
    "shot_table.csv",
    "image_prompts.csv",
    "video_prompts.csv",
    "voice_lines.csv",
    "sound_plan.csv",
    "edit_plan.json",
)

PROJECT_DIRS = (
    "assets/references",
    "assets/storyboards",
    "assets/video_clips",
    "assets/audio",
    "assets/exports",
    "requests/pending",
    "requests/completed",
    "outputs/script",
    "outputs/characters",
    "outputs/shot_table",
    "outputs/image_prompts",
    "outputs/video_prompts",
    "outputs/sound",
    "outputs/edit",
)

GENERATION_MODES = ("manual_file", "codex_web", "api_command")

