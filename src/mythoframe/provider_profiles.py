"""Provider routing defaults for web/manual generation requests."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_PROVIDER_PROFILE = "seedance-first"


@dataclass(frozen=True)
class StageProvider:
    target_site: str
    target_model: str
    operator_notes: str


SEEDANCE_FIRST_STAGE_PROVIDERS: dict[str, StageProvider] = {
    "adaptation": StageProvider(
        target_site="ChatGPT web or OpenAI",
        target_model="gpt-4.1-mini for cheap testing; stronger model if quality needs it",
        operator_notes="Text planning stage. No media generation required.",
    ),
    "script": StageProvider(
        target_site="ChatGPT web or OpenAI",
        target_model="gpt-4.1-mini for cheap testing; stronger model if quality needs it",
        operator_notes="Text planning stage. Keep the script short enough for a 60-90 second short.",
    ),
    "characters": StageProvider(
        target_site="ChatGPT web or OpenAI",
        target_model="gpt-4.1-mini for cheap testing; stronger model if quality needs it",
        operator_notes="Create character bible and reference prompts before image generation.",
    ),
    "shot_table": StageProvider(
        target_site="ChatGPT web or OpenAI",
        target_model="gpt-4.1-mini for cheap testing; stronger model if quality needs it",
        operator_notes="Break the scene into simple 16:9 cinematic shots, usually around 3 seconds each.",
    ),
    "image_prompts": StageProvider(
        target_site="ChatGPT Images, Gemini/Nano Banana, or Seedream",
        target_model="chosen image provider",
        operator_notes="Generate character references and selected keyframes/storyboards before Seedance video.",
    ),
    "video_prompts": StageProvider(
        target_site="Seedance-capable web platform",
        target_model="Seedance 2.0",
        operator_notes=(
            "Seedance-first video stage. Prefer a web UI such as Runway, Higgsfield, "
            "or an official ByteDance/BytePlus UI if available; avoid direct API "
            "unless explicitly chosen. Prefer image-to-video from selected storyboard "
            "frames and use native audio where useful."
        ),
    ),
    "sound_plan": StageProvider(
        target_site="Seedance-capable web platform first; optional specialist audio fallback",
        target_model="Seedance 2.0 native audio-video; ElevenLabs/Suno/Udio only if needed",
        operator_notes="Plan sound for Seedance native clip audio first. Add separate voice/music tools only if Seedance control is insufficient.",
    ),
    "edit_plan": StageProvider(
        target_site="Local ffmpeg after Seedance downloads",
        target_model="local render/export",
        operator_notes="Assemble local assets. Seedance outputs should be imported before rough-cut rendering.",
    ),
}


def provider_profile_names() -> tuple[str, ...]:
    return (DEFAULT_PROVIDER_PROFILE,)


def stage_provider(stage: str, profile: str = DEFAULT_PROVIDER_PROFILE) -> StageProvider:
    if profile != DEFAULT_PROVIDER_PROFILE:
        valid = ", ".join(provider_profile_names())
        raise ValueError(f"Unknown provider profile `{profile}`. Valid profiles: {valid}")
    try:
        return SEEDANCE_FIRST_STAGE_PROVIDERS[stage]
    except KeyError as exc:
        valid = ", ".join(SEEDANCE_FIRST_STAGE_PROVIDERS)
        raise ValueError(f"Unknown stage `{stage}`. Valid stages: {valid}") from exc
