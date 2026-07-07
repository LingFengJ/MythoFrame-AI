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
- Video/audio-video provider: a Seedance 2.0-capable web platform.
- Local `ffmpeg`: local rough-cut assembly.

## Seedance Access Route

Use a Seedance-capable web UI first, not a direct API. Suitable starting points
include Runway, Higgsfield, or an official ByteDance/BytePlus/Volcengine UI if
one is available to the account. This matches the project design: Codex or the
human operator prepares prompts, uploads references, downloads generated clips,
and imports the assets back into MythoFrame.

Direct API access is a later automation backend. Add it only when the user
explicitly chooses API automation, accepts the cost/onboarding requirements, and
provides the needed account credentials.

Current public notes verified on 2026-07-07:

- ByteDance's official Seedance 2.0 page exposes both try-now and API paths:
  https://seed.bytedance.com/en/seedance2_0
- Runway's Seedance 2.0 help page documents web-app access for Standard plan or
  higher, with text, image, video, and audio inputs:
  https://help.runwayml.com/hc/en-us/articles/50488490233363-Creating-with-Seedance-2-0
- Seedance 2.0 is designed for native audio-video generation, so specialist
  voice/music tools should stay optional until a pilot proves they are needed.

Third-party web platforms can be easier or cheaper for early production because
they package model access into subscriptions/credits, abstract API setup, queue
jobs, limit resolution/modes by plan, and may have provider partnerships. That
does not prove the official API is always more expensive; it means the API path
has more integration, account, pricing, and usage-risk overhead for this manual
workflow.

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
Seedance 2.0-capable web platform
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
| `video_prompts` | Seedance-capable web platform, target model Seedance 2.0 |
| `sound_plan` | Seedance native audio-video first, specialist audio only if needed |
| `edit_plan` | Local ffmpeg after Seedance downloads |
