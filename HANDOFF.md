# MythoFrame AI Handoff

Use this file as the first read for any new Codex agent continuing this project.
It is both project status and operating guidance.

## Current Snapshot

- Date of snapshot: 2026-07-07
- Repository: `https://github.com/LingFengJ/MythoFrame-AI`
- Main branch status: run `git log --oneline -5` for the current commit. This
  handoff is intended to be updated when project architecture changes.
- Owner Git identity used locally:
  - Name: `LingFengJ`
  - Email: `jinlingfeng2579@gmail.com`
- Product direction: AI-assisted workflow for turning stories, novels, manga
  scripts, and original ideas into cinematic animated shorts.
- First production target:
  - Horizontal `16:9`
  - `60-90 seconds`
  - Cinematic animated short
  - Source book, manga, or story still to be selected

## Important Product Decision

Paid API generation must not be the default.

The user explicitly wants the project to support high-quality web model usage
without forcing expensive API calls. The preferred generation order is:

1. `manual_file`: create prompt and response files; user pastes model output.
2. `codex_web`: Codex operates model websites through browser use when possible,
   or computer use when browser automation is not enough.
3. `api_command`: opt-in only, through a user-configured wrapper command.

Never wire a paid API provider as the default path. Never make background API
calls without explicit user approval.

## What Exists Now

Tracked project backbone:

- `README.md`: overview and quickstart.
- `pyproject.toml`: no-dependency Python package config.
- `.env.example`: optional API command wrapper setting.
- `.gitignore`: ignores local envs, caches, generated project assets, request
  queues, and outputs.
- `src/mythoframe/cli.py`: CLI entrypoint.
- `src/mythoframe/project.py`: project skeleton creation and validation.
- `src/mythoframe/manual_queue.py`: file-based request/response queue.
- `src/mythoframe/artifacts.py`: applies collected outputs to canonical project
  artifacts with validation rollback.
- `src/mythoframe/output_tools.py`: inspects and mechanically repairs collected
  model outputs before application.
- `src/mythoframe/providers.py`: opt-in command-based API provider hook.
- `src/mythoframe/prompts.py`: stage template rendering.
- `src/mythoframe/assets.py`: asset naming conventions.
- `src/mythoframe/bundle.py`: project pack/unpack helpers for moving ignored
  local work between machines.
- `src/mythoframe/pilot.py`: offline original pilot scaffolding.
- `src/mythoframe/workflow.py`: stage status and review helpers.
- `src/mythoframe/timeline.py`: local edit-plan and manifest helpers.
- `src/mythoframe/subtitles.py`: SRT/VTT subtitle export helpers.
- `src/mythoframe/renderer.py`: optional local `ffmpeg` rough-cut renderer.
- `src/mythoframe/schemas.py`: shared constants.
- `docs/architecture.md`: file-first architecture and project truth boundary.
- `docs/workflow.md`: pilot/review/validation/export workflow.
- `docs/stage_prompts.md`: stage prompt commands and template behavior.
- `docs/assets.md`: asset naming conventions.
- `docs/generation_modes.md`: manual, Codex web, and API command modes.
- `docs/codex_handoff.md`: how Codex should operate pending web/manual
  generation requests.
- `prompts/stages/`: editable prompt templates for the production stages.
- `examples/pilot_brief.md`: pilot brief template.
- `tests/test_backbone.py`: smoke tests for project init, queue collection, and
  CLI init/validate, bundles, output inspection, subtitles, and rough-cut
  preflight behavior.

Local-only files seen in the original Windows worktree:

- Two `.docx` workflow guide files used as source planning notes.
- `AGENTS.md`, a large untracked local repository instruction file.

Do not assume those local-only files exist after cloning on another machine.
If they are present, inspect them before relying on them. Do not accidentally
commit large local instruction or source-document files unless the user asks.

## How To Run

From the repository root:

```powershell
python -m unittest discover -s tests
python -m compileall src tests
```

Install locally:

```powershell
python -m pip install -e .
```

Create a pilot project:

```powershell
mythoframe init pilot-scene --title "Pilot Scene"
```

Or create the offline original pilot:

```powershell
mythoframe pilot pilot-scene
```

Create a manual request:

```powershell
mythoframe request pilot-scene script --prompt-file examples/pilot_brief.md
```

Create a stage-specific request:

```powershell
mythoframe request-stage pilot-scene script
```

Render a prompt without creating a request:

```powershell
mythoframe prompt pilot-scene script
```

Review status:

```powershell
mythoframe review pilot-scene
```

Create the next request automatically:

```powershell
mythoframe next pilot-scene
```

After a model response is pasted below the marker in the generated response
file:

```powershell
mythoframe collect pilot-scene
mythoframe inspect-output pilot-scene script
mythoframe apply-output pilot-scene script
```

If the collected output is parseable but messy:

```powershell
mythoframe repair-output pilot-scene script
mythoframe apply-output pilot-scene script --output-file projects/pilot-scene/outputs/script/<id>.repaired.md
```

Create and export local edit planning artifacts:

```powershell
mythoframe draft-edit pilot-scene
mythoframe export-manifest pilot-scene
```

Export subtitles:

```powershell
mythoframe subtitles pilot-scene --format srt
mythoframe subtitles pilot-scene --format vtt
```

Render a rough cut when `ffmpeg` exists and local video assets are present:

```powershell
mythoframe render-rough-cut pilot-scene
```

Pack or unpack a local project, including generated ignored work:

```powershell
mythoframe pack pilot-scene
mythoframe unpack bundles/pilot-scene_YYYYMMDDTHHMMSSZ.mythoframe.zip
```

Create a Codex-assisted web request:

```powershell
mythoframe request pilot-scene script --mode codex_web --prompt-file examples/pilot_brief.md
```

Use API automation only when explicitly configured:

```powershell
$env:MYTHOFRAME_API_COMMAND = "C:\path\to\wrapper.exe"
mythoframe request pilot-scene script --mode api_command --prompt-file examples/pilot_brief.md
```

The wrapper contract is:

```text
wrapper prompt-file-path output-file-path
```

## Design Principles To Preserve

- File-first and reviewable: prompts, responses, project truth, and generated
  assets should stay inspectable.
- API-last: web/manual/Codex workflows are first-class, not temporary hacks.
- Provenance matters: do not silently treat raw model output as final project
  truth.
- Consistency matters most: character bible and shot bible should drive image
  and video prompts.
- Each shot should usually be one simple action or emotion, around three
  seconds or less.
- Sound is its own production layer: voice, narration, music, ambience, SFX,
  subtitles, timing, and loudness should be structured, not an afterthought.
- Editing should start as an edit decision list before any renderer is added.
- Keep generated source material, copyrighted excerpts, API keys, and account
  credentials out of commits.

## Browser And Computer Use Policy

When Codex is asked to operate model websites:

- Prefer browser automation for browser pages.
- Use computer use only when browser automation cannot handle the UI.
- If neither works, keep the response file empty and let the user paste output.
- Confirm before uploading copyrighted/private source material to third-party
  sites.
- Confirm before any paid generation, subscription, account creation, purchase,
  or API-key creation.
- Do not paste secrets into model websites or committed files.

The project itself does not directly control Codex browser/computer-use tools.
It creates durable request files that a Codex agent can operate against.

## Likely Next Engineering Steps

Good next steps, in order:

1. Add stage-specific prompt templates for script, character bible, shot table,
   image prompts, video prompts, sound plan, and edit plan. Done.
2. Add a command to generate those prompts from a project bible and source
   brief. Done.
3. Add schema validation for CSV/JSON artifacts beyond file existence. Initial
   row-level validation exists; deepen it as schemas become stricter.
4. Add a rough-cut edit plan schema before implementing any renderer. Done:
   initial schema, prompt, local draft builder, manifest export, subtitle
   export, and optional `ffmpeg` renderer exist.
5. Add project bundle import/export for generated work ignored by Git. Done.
6. Add collected-output inspection and mechanical repair helpers. Done.
7. Add a small local web UI only after the CLI workflow is solid.
8. Add provider adapters last, keeping them opt-in and disabled by default.

## Current Risks

- Offline original pilot scaffolding exists, but no user-selected source project
  has been created yet.
- No book, manga, or user-owned story source has been selected.
- No provider web workflows have been tested against live model sites.
- Rough-cut rendering exists, but it has not been exercised with real generated
  clips in a production project.
- Asset naming conventions exist, but no real generated assets have been linked
  through a production project yet.
- `projects/*/requests`, `projects/*/outputs`, and `projects/*/assets` are
  ignored, so generated work products are local unless bundled, separately
  exported, or explicitly tracked.

## How A New Agent Should Start

1. Run `git status --short`.
2. Read `README.md`.
3. Read this `HANDOFF.md`.
4. Read `docs/architecture.md`, `docs/generation_modes.md`, and
   `docs/codex_handoff.md`.
5. Inspect `src/mythoframe` before changing behavior.
6. Run the tests before and after edits when feasible.
7. Keep commits narrow and do not stage local-only `.docx`, generated assets,
   request queues, response outputs, `.env` files, or unrelated user changes.
