# Provider Plan

Default profile: `seedance-first`.

`mythoframe request-stage` and `mythoframe next` use this profile by default.
The request metadata tells a human or Codex operator which site/model should be
used for the stage. You can override this per request with `--target-site`,
`--target-model`, or `--operator-notes`.

## Minimum Accounts

- GitHub: source control and project continuity.
- Text/planning model: ChatGPT web or OpenAI, for adaptation, script, shot
  table, image prompts, video prompts, sound plan, and edit plan.
- Image provider: choose one of ChatGPT Images, Gemini/Nano Banana, or Seedream.
- Video/audio-video provider: Seedance 2.0.
- Local `ffmpeg`: local rough-cut assembly.

## Seedance Role

Assume Seedance is the main video tool. Use it for:

- text-to-video when no reference image is needed,
- image-to-video from selected storyboard/keyframes,
- native generated clip audio when it is good enough,
- multimodal reference workflows where the UI/account supports them.

Seedance can reduce the need for separate audio accounts because Seedance 2.0
supports joint audio-video generation. It should be tested first before adding
specialized sound tools.

## Optional Accounts

These are not baseline requirements:

- ElevenLabs: use only if Seedance audio is not enough for clean dialogue,
  narration, dubbing, or separate voice files.
- Suno or Udio: use only if Seedance audio is not enough for controllable music.
- Fish Audio or CapCut voice tools: optional voice/dubbing alternatives.

## Practical Rule

Start with:

```text
GitHub
ChatGPT/OpenAI
one image provider: ChatGPT Images or Gemini/Nano Banana or Seedream
Seedance 2.0
ffmpeg
```

Add specialist audio/music accounts only after one real pilot proves they are
needed.

## Stage Routing Defaults

| Stage | Default target |
| --- | --- |
| `adaptation` | ChatGPT web or OpenAI |
| `script` | ChatGPT web or OpenAI |
| `characters` | ChatGPT web or OpenAI |
| `shot_table` | ChatGPT web or OpenAI |
| `image_prompts` | ChatGPT Images, Gemini/Nano Banana, or Seedream |
| `video_prompts` | Seedance 2.0 |
| `sound_plan` | Seedance 2.0 first, specialist audio only if needed |
| `edit_plan` | Local ffmpeg after Seedance downloads |
