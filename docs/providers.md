# Provider Plan

Default profile: `seedance-first`.

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
