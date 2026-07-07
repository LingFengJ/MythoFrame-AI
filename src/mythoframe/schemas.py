"""Shared schema names and filesystem conventions."""

from __future__ import annotations

OUTPUT_MARKER = "<!-- MODEL_OUTPUT_BELOW -->"

ARTIFACT_STATUSES = (
    "draft",
    "pending",
    "generated",
    "selected",
    "needs_review",
    "approved",
    "rejected",
)

SOUND_CUE_TYPES = ("music", "ambience", "sfx", "mix_note")

STAGE_NAMES = (
    "adaptation",
    "script",
    "characters",
    "shot_table",
    "image_prompts",
    "video_prompts",
    "sound_plan",
    "edit_plan",
)

PROJECT_FILES = (
    "source_brief.md",
    "adaptation.md",
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
    "assets/audio/voice",
    "assets/audio/sfx",
    "assets/audio/music",
    "assets/exports",
    "requests/pending",
    "requests/completed",
    "outputs/adaptation",
    "outputs/script",
    "outputs/characters",
    "outputs/shot_table",
    "outputs/image_prompts",
    "outputs/video_prompts",
    "outputs/sound_plan",
    "outputs/edit_plan",
    "outputs/edit",
)

GENERATION_MODES = ("manual_file", "codex_web", "api_command")

CSV_REQUIRED_HEADERS = {
    "shot_table.csv": (
        "shot_number",
        "duration",
        "camera_movement",
        "framing",
        "visual_description",
        "image_prompt",
        "video_prompt",
        "dialogue",
        "narration",
        "music",
        "sound_effects",
        "review_status",
    ),
    "image_prompts.csv": (
        "shot_number",
        "candidate_id",
        "prompt",
        "reference_assets",
        "negative_prompt",
        "status",
        "selected_asset",
    ),
    "video_prompts.csv": (
        "shot_number",
        "source_image",
        "prompt",
        "duration",
        "status",
        "selected_clip",
    ),
    "voice_lines.csv": (
        "line_id",
        "shot_number",
        "speaker",
        "text",
        "voice_style",
        "status",
        "audio_asset",
    ),
    "sound_plan.csv": (
        "cue_id",
        "shot_number",
        "cue_type",
        "description",
        "timing",
        "status",
        "audio_asset",
    ),
}

CSV_REQUIRED_ROW_FIELDS = {
    "shot_table.csv": ("shot_number", "duration", "visual_description", "review_status"),
    "image_prompts.csv": ("shot_number", "candidate_id", "prompt", "status"),
    "video_prompts.csv": ("shot_number", "source_image", "prompt", "duration", "status"),
    "voice_lines.csv": ("line_id", "shot_number", "speaker", "text", "status"),
    "sound_plan.csv": ("cue_id", "shot_number", "cue_type", "description", "status"),
}

CSV_INTEGER_FIELDS = {
    "shot_table.csv": ("shot_number",),
    "image_prompts.csv": ("shot_number",),
    "video_prompts.csv": ("shot_number",),
    "voice_lines.csv": ("line_id", "shot_number"),
    "sound_plan.csv": ("shot_number",),
}

CSV_STATUS_FIELDS = {
    "shot_table.csv": ("review_status",),
    "image_prompts.csv": ("status",),
    "video_prompts.csv": ("status",),
    "voice_lines.csv": ("status",),
    "sound_plan.csv": ("status",),
}
