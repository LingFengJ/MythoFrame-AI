# Architecture

MythoFrame separates planning, generation, review, and editing.

## Backbone

```text
source material
  -> project bible
  -> script
  -> character bible
  -> shot table
  -> image prompts
  -> selected images
  -> video prompts
  -> selected clips
  -> sound plan
  -> edit plan
  -> final export
```

The first implementation focuses on structured files and durable handoffs. This
keeps the workflow usable even when model websites change, API prices are high,
or a step needs human review.

## Project Folder

```text
projects/<slug>/
  source_brief.md
  adaptation.md
  project_bible.json
  characters.json
  script.md
  shot_table.csv
  image_prompts.csv
  video_prompts.csv
  voice_lines.csv
  sound_plan.csv
  edit_plan.json
  assets/
  requests/
  outputs/
```

## Why File-Based First

The expensive part of this workflow is model generation. The file queue makes
generation explicit:

- every prompt is inspectable before it is sent anywhere
- every response can be reviewed before it becomes project truth
- Codex/web/manual/API workflows share the same artifact structure
- API automation can be added without making it the default path

## Editing Layer

Editing should be represented as an edit decision list before rendering. The
rough-cut renderer can later consume `edit_plan.json` and asset paths to produce
an automated assembly with `ffmpeg` or an editing application's timeline format.

The final edit should still have a review gate because shot rhythm, continuity,
and emotional pacing are not reliably solved by automation alone.

## Prompt Layer

Stage prompts live in `prompts/stages/`. They can be rendered without calling a
model:

```powershell
mythoframe prompt <slug> <stage>
```

They can also be turned into manual, Codex-assisted, or opt-in API requests:

```powershell
mythoframe request-stage <slug> <stage> --mode manual_file
mythoframe request-stage <slug> <stage> --mode codex_web
mythoframe request-stage <slug> <stage> --mode api_command
```
