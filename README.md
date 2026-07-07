# MythoFrame AI

MythoFrame AI is an AI-assisted production workflow for turning stories, novels,
manga scripts, and original ideas into cinematic animated shorts.

The first target is horizontal video content, roughly 60-90 seconds per short.
The source material, visual style, and publishing plan will be selected per
project once a book, manga, script, or original premise is chosen.

## Goal

Build a repeatable pipeline that can move from source material to a finished
short through structured stages:

1. Story intake and adaptation
2. Short-form scriptwriting
3. Character design and character bible
4. Shot list and storyboard planning
5. Image prompt generation
6. Image generation and visual selection
7. Image-to-video prompt generation
8. Video clip generation
9. Voice, narration, music, and sound effects
10. Editing, subtitles, pacing, transitions, and final export

## First Production Format

- Aspect ratio: horizontal 16:9
- Runtime: 60-90 seconds
- Output style: cinematic animated short
- Source type: to be determined
- Workflow priority: consistency first, then quality, then speed

## Core Workflow

### 1. Adaptation

The workflow starts by converting a story idea or source excerpt into a compact
short-film structure. For adapted material, the pipeline should identify the
main conflict, characters, scene goal, emotional arc, and the specific moment
that can fit inside a 60-90 second short.

### 2. Script

The script stage produces dialogue, narration, scene beats, emotional tone, and
visual intent. The output should be short enough to become a shot table rather
than a full screenplay.

### 3. Character Bible

Character consistency is one of the hardest parts of AI video production. Each
main character needs a reusable character bible with:

- Name and role
- Age range and body type
- Face shape and key facial features
- Hair, costume, color palette, and accessories
- Personality and emotional range
- Reference image prompts
- Negative or correction prompts for unwanted drift

### 4. Storyboard And Shot Table

The script is converted into a structured shot table. Each shot should usually
do one clear thing and stay under about three seconds.

Recommended shot table fields:

- Shot number
- Duration
- Camera movement
- Framing
- Visual description
- Image generation prompt
- Image-to-video prompt
- Dialogue
- Narration
- Music direction
- Sound effects
- Notes and review status

### 5. Image Generation

The image stage creates character references and storyboard frames. The pipeline
should generate several candidates per shot, then select the best option based
on character consistency, composition, style match, and story clarity.

### 6. Video Generation

Each selected storyboard frame becomes a short video clip. Image-to-video prompts
should describe specific motion: character action, camera movement, emotion
change, environmental movement, and pacing.

## Can Editing Be Automated By AI?

Yes, editing can be partially automated, but it should be treated as a supervised
assembly process rather than a single button.

Automatable editing tasks include:

- Ordering clips by shot number
- Trimming clips to planned duration
- Matching video clips to dialogue and narration timing
- Adding subtitles
- Placing music and sound effects on a timeline
- Adding simple transitions
- Normalizing audio loudness
- Creating rough cuts with `ffmpeg` or an editing API
- Exporting review versions

Tasks that usually need human review:

- Choosing the best generated clip
- Fixing awkward motion
- Deciding emotional pacing
- Adjusting shot rhythm
- Removing continuity errors
- Balancing music, dialogue, and sound effects

The practical approach is to make AI generate an edit decision list first. That
edit plan can then be rendered automatically with tools like `ffmpeg`, or later
translated into a timeline for CapCut, Premiere Pro, DaVinci Resolve, or another
editor.

## What About Sound?

Sound should be designed as its own production layer, not added at the end as an
afterthought.

The sound workflow should include:

- Dialogue lines per character
- Narration lines
- Voice casting and voice style
- Background music direction
- Environmental ambience
- Specific sound effects per shot
- Timing notes
- Subtitle text
- Loudness and final mix checks

AI can help generate voice, narration, music direction, sound-effect lists, and
timed subtitle files. The pipeline should keep these as structured assets so
each shot has both visual and audio intent.

## Initial Technical Plan

The first version should focus on producing clean production files before trying
to automate every external platform.

Suggested MVP outputs:

- `project_bible.json`
- `characters.json`
- `script.md`
- `shot_table.csv`
- `image_prompts.csv`
- `video_prompts.csv`
- `voice_lines.csv`
- `sound_plan.csv`
- `edit_plan.json`

Once these files are reliable, provider integrations can be added for web UI
operation or opt-in APIs covering large language models, image generation,
video generation, voice generation, music, storage, and final rendering.

## Accounts Eventually Needed

Baseline:

- GitHub account for source control
- ChatGPT web or OpenAI access for script, prompt, and planning work
- One image generation web account: ChatGPT Images, Gemini/Nano Banana, or
  Seedream
- Dreamina/CapCut access for Seedance 2.0 video and native audio-video clips
- Local `ffmpeg` for rough-cut rendering

Optional later:

- API keys for any provider the user explicitly wants to automate
- Voice generation account if Seedance native audio is not clean enough
- Music or sound-effect source if Seedance is not controllable enough
- Cloud storage for generated assets
- Web app hosting
- Database hosting
- Social media publishing accounts
- Editing software integration
- Upscaling service or desktop tool

API keys should be stored in environment variables or `.env` files and should
never be committed to GitHub.

## Current Status

This repository now has a manual-first engineering backbone with project
bundles, stage prompts, collected-output inspection, subtitle export, rough-cut
render hooks, generated-asset import/selection, missing-media checks, request
dashboards, and a local edit manifest flow.

## Quickstart

Install locally in editable mode:

```powershell
python -m pip install -e .
```

Create a first project:

```powershell
mythoframe init pilot-scene --title "Pilot Scene"
```

Or create an offline original pilot project:

```powershell
mythoframe pilot pilot-scene
```

Create a default manual generation request:

```powershell
mythoframe request pilot-scene script --prompt-file examples/pilot_brief.md
```

Create a stage-specific request from project files:

```powershell
mythoframe request-stage pilot-scene script
```

Stage requests use the `seedance-first` provider profile by default: planning
stages target ChatGPT/OpenAI, image prompts target your chosen image provider,
and video/sound planning targets Dreamina/CapCut Seedance first.

The safe CLI default is `manual_file`, but the normal production path with Codex
is `codex_web`: Codex prepares the request, tries browser automation first,
uses computer-use automation only when the site requires it, and falls back to
manual paste/download if the provider blocks automation.

Or ask the CLI to choose the next incomplete stage:

```powershell
mythoframe next pilot-scene
```

Paste the model output into the generated `.response.md` file below the marker,
then collect it:

```powershell
mythoframe collect pilot-scene
mythoframe inspect-output pilot-scene script
mythoframe repair-output pilot-scene script
mythoframe apply-output pilot-scene script
```

`inspect-output` checks whether the latest collected output can be parsed for
that stage. `repair-output` writes a normalized `.repaired.md` file when the
model returned useful content with extra surrounding text.

For Codex-assisted web generation, use:

```powershell
mythoframe request pilot-scene script --mode codex_web --prompt-file examples/pilot_brief.md
```

Then ask Codex to process the pending request. Codex can use browser automation,
computer-use automation, or fall back to a manual paste workflow.

For opt-in API automation, set `MYTHOFRAME_API_COMMAND` to a local wrapper
command and use `--mode api_command`. This is intentionally not the default.

Review current project status:

```powershell
mythoframe review pilot-scene
mythoframe requests pilot-scene --completed
mythoframe doctor pilot-scene
mythoframe guide pilot-scene
mythoframe providers
```

Import generated assets downloaded from model websites:

```powershell
mythoframe import-asset pilot-scene storyboard ./downloads/shot1.png --shot 1 --candidate-id shot_001_a --provider "ImageSite"
mythoframe import-asset pilot-scene video_clip ./downloads/shot1.mp4 --shot 1 --candidate-id shot_001_clip_a --provider "Dreamina Seedance 2.0"
mythoframe select-asset pilot-scene shot_001_a
mythoframe select-asset pilot-scene shot_001_clip_a
mythoframe assets pilot-scene
mythoframe missing-media pilot-scene
```

Build a local edit decision list and export a text manifest:

```powershell
mythoframe draft-edit pilot-scene
mythoframe export-manifest pilot-scene
```

Export subtitles:

```powershell
mythoframe subtitles pilot-scene --format srt
mythoframe subtitles pilot-scene --format vtt
```

Render a rough cut when `ffmpeg` is installed and the edit plan points to real
local video clips:

```powershell
mythoframe render-rough-cut pilot-scene
```

Move a local project between machines, including ignored outputs and generated
assets:

```powershell
mythoframe pack pilot-scene
mythoframe unpack bundles/pilot-scene_YYYYMMDDTHHMMSSZ.mythoframe.zip
```

See:

- `COMMANDS.md`
- `HANDOFF.md`
- `docs/architecture.md`
- `docs/workflow.md`
- `docs/stage_prompts.md`
- `docs/generation_modes.md`
- `docs/codex_handoff.md`
- `docs/assets.md`
- `docs/providers.md`
