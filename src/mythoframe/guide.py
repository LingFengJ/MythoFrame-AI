"""Human-readable command and provider guides."""

from __future__ import annotations


def command_guide(slug: str = "pilot-scene") -> str:
    return f"""# MythoFrame Command Guide

## Normal Planning Loop

mythoframe pilot {slug}
mythoframe review {slug}
mythoframe next {slug}
mythoframe collect {slug}
mythoframe inspect-output {slug} <stage>
mythoframe apply-output {slug} <stage>
mythoframe validate {slug}

Repeat `next -> collect -> inspect-output -> apply-output -> validate` through:

adaptation -> script -> characters -> shot_table -> image_prompts -> video_prompts -> sound_plan -> edit_plan

## Seedance-First Media Loop

Use Seedance for generated video clips and native clip audio whenever possible.
Use one image provider for references/keyframes: ChatGPT Images, Gemini/Nano Banana, or Seedream.
`request-stage` and `next` use the seedance-first provider profile by default.

mythoframe import-asset {slug} storyboard <downloaded-image> --shot 1 --candidate-id shot_001_a --provider "<image provider>"
mythoframe select-asset {slug} shot_001_a
mythoframe import-asset {slug} video_clip <seedance-video> --shot 1 --candidate-id shot_001_clip_a --provider "Seedance 2.0"
mythoframe select-asset {slug} shot_001_clip_a
mythoframe assets {slug}
mythoframe missing-media {slug}

## Editing And Export

mythoframe draft-edit {slug}
mythoframe subtitles {slug} --format srt
mythoframe export-manifest {slug}
mythoframe render-rough-cut {slug}
mythoframe pack {slug}

## Readiness

mythoframe requests {slug} --completed
mythoframe doctor {slug}
"""


def provider_guide() -> str:
    return """# MythoFrame Provider Profile: seedance-first

## Required Minimum

- GitHub: source control.
- Text/planning model: ChatGPT web or OpenAI, used for scripts, prompt plans, shot tables, sound plans, and edit plans.
- Image provider: choose one of ChatGPT Images, Gemini/Nano Banana, or Seedream.
- Video/audio-video provider: Seedance 2.0, used for image-to-video/text-to-video and native clip audio where possible.
- Local ffmpeg: local rough-cut assembly.

## Not Required At First

- ElevenLabs: optional if Seedance native audio is not enough for clean dialogue, narration, dubbing, or separate voice tracks.
- Suno/Udio: optional if Seedance native audio is not enough for controllable music.
- Fish Audio/CapCut voice tools: optional voice/dubbing alternatives.

## Practical Rule

Start with the minimum stack. Add specialist audio/music accounts only after a real pilot proves Seedance cannot provide enough control for dialogue, narration, music, sound effects, or final mix needs.
"""
