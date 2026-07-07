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
- Video/audio-video provider: Dreamina/CapCut first, with Runway or
  seedance2.ai as fallbacks.
- Local `ffmpeg`: local rough-cut assembly.

## Seedance Access Route

Use a web UI first, not a direct API. The current preferred order is:

1. Dreamina/CapCut: first provider to test. It appears to be the closest
   official consumer web route for Seedance because the Dreamina site is under
   `dreamina.capcut.com` and links to CapCut terms.
2. Runway: reliable professional fallback with public Seedance 2.0 docs,
   clear plan pricing, and documented text/image/video/audio inputs.
3. seedance2.ai: cheap transparent-credit candidate, but unofficial. Test
   payment safety, export quality, model parity, and support before relying on
   it for production.
4. Direct ByteDance/BytePlus/Volcengine API: later automation/backend path
   only after explicit user choice.

This matches the project design: Codex or the human operator prepares prompts,
uploads references, downloads generated clips, and imports the assets back into
MythoFrame.

Direct API access is a later automation backend. Add it only when the user
explicitly chooses API automation, accepts the cost/onboarding requirements, and
provides the needed account credentials.

Current public notes verified on 2026-07-07:

- ByteDance's official Seedance 2.0 page exposes both try-now and API paths:
  https://seed.bytedance.com/en/seedance2_0
- Dreamina/CapCut exposes Dreamina Seedance models, free daily credits, and an
  AI video web workflow:
  https://dreamina.capcut.com/tools/ai-video-generator
- Dreamina also advertises Seedance 2.5. Treat it as a candidate upgrade only
  after a pilot comparison; keep Seedance 2.0 as the baseline request target
  until real outputs prove 2.5 is better for this workflow.
- Runway's Seedance 2.0 help page documents web-app access for Standard plan or
  higher, with text, image, video, and audio inputs:
  https://help.runwayml.com/hc/en-us/articles/50488490233363-Creating-with-Seedance-2-0
- seedance2.ai publishes low-friction credit pricing but states in its terms
  that it is independent and not affiliated with ByteDance:
  https://seedance2.ai/pricing
  https://seedance2.ai/terms-of-service
- Seedance 2.0 is designed for native audio-video generation, so specialist
  voice/music tools should stay optional until a pilot proves they are needed.

Third-party web platforms can be easier or cheaper for early production because
they package model access into subscriptions/credits, abstract API setup, queue
jobs, limit resolution/modes by plan, and may have provider partnerships. That
does not prove the official API is always more expensive; it means the API path
has more integration, account, pricing, and usage-risk overhead for this manual
workflow.

## Provider Comparison Snapshot

| Provider | Role | Current concern |
| --- | --- | --- |
| Dreamina/CapCut | First provider to test; closest official consumer route found so far | Public page confirms free daily credits, but exact paid credit math needs login verification |
| Runway | Reliable professional fallback | Clear pricing and docs, but 1080p Seedance uses credits and can be costly for retries |
| seedance2.ai | Cheap experimental fallback | Transparent low-friction pricing, but terms say it is independent from ByteDance |
| ByteDance/BytePlus/Volcengine API | Later automation/backend route | Not the manual default; requires explicit cost, onboarding, and credential decisions |

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
Dreamina/CapCut for Seedance 2.0
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
| `video_prompts` | Dreamina/CapCut first; Runway or seedance2.ai fallback, target model Seedance 2.0 |
| `sound_plan` | Dreamina/Seedance native audio-video first, specialist audio only if needed |
| `edit_plan` | Local ffmpeg after Seedance downloads |
