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

Once these files are reliable, provider integrations can be added for large
language models, image generation, video generation, voice generation, music,
storage, and final rendering.

## Accounts And Keys Eventually Needed

Likely required:

- GitHub account for source control
- LLM API key for script, prompt, and planning automation
- Image generation account or API
- Video generation account or API
- Voice generation account or API
- Music or sound-effect source
- Cloud storage for generated assets

Optional later:

- Web app hosting
- Database hosting
- Social media publishing accounts
- Editing software integration
- Upscaling service or desktop tool

API keys should be stored in environment variables or `.env` files and should
never be committed to GitHub.

## Current Status

This repository now has a manual-first engineering backbone.

## Quickstart

Install locally in editable mode:

```powershell
python -m pip install -e .
```

Create a first project:

```powershell
mythoframe init pilot-scene --title "Pilot Scene"
```

Create a default manual generation request:

```powershell
mythoframe request pilot-scene script --prompt-file examples/pilot_brief.md
```

Paste the model output into the generated `.response.md` file below the marker,
then collect it:

```powershell
mythoframe collect pilot-scene
```

For Codex-assisted web generation, use:

```powershell
mythoframe request pilot-scene script --mode codex_web --prompt-file examples/pilot_brief.md
```

Then ask Codex to process the pending request. Codex can use browser automation,
computer-use automation, or fall back to a manual paste workflow.

For opt-in API automation, set `MYTHOFRAME_API_COMMAND` to a local wrapper
command and use `--mode api_command`. This is intentionally not the default.

See:

- `docs/architecture.md`
- `docs/generation_modes.md`
- `docs/codex_handoff.md`
