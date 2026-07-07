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
- `src/mythoframe/media.py`: imports generated media, tracks asset candidates,
  selects/rejects candidates, updates consumption artifacts, and reports missing
  media.
- `src/mythoframe/diagnostics.py`: operational readiness checks, including
  optional tiny OpenAI API smoke testing.
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
  preflight behavior, request metadata, asset import/selection, missing media,
  and diagnostics.

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
mythoframe requests pilot-scene --completed
mythoframe doctor pilot-scene
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

Import, select, and inspect generated media:

```powershell
mythoframe import-asset pilot-scene storyboard .\downloads\shot1.png --shot 1 --candidate-id shot_001_a --provider "ImageSite"
mythoframe select-asset pilot-scene shot_001_a
mythoframe assets pilot-scene
mythoframe missing-media pilot-scene
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

## Direction Check

The current direction is correct for the user's goal: make the project usable
with logged-in web accounts first, while keeping API automation optional and
off by default.

The right target state is not "one hidden script calls every provider." The
right target state is:

1. The project owns the structured production truth.
2. Humans or Codex operate high-quality model websites from durable request
   files.
3. Every external output is collected, inspected, repaired if needed, and only
   then promoted into canonical project artifacts.
4. Generated media is imported, selected, and registered in the project before
   editing.
5. A local renderer or export manifest can assemble a reviewable cut once the
   logged-in accounts have produced the needed clips and sound.

This approach is slower than direct API automation, but it matches the cost
constraint and keeps the workflow resilient when model websites, prices, or
terms change.

## Done

Current completed backbone:

- Repository, README, docs, tests, and GitHub remote are set up.
- Manual-first project skeleton exists.
- Offline original pilot scaffold exists.
- Stage prompt templates exist for `adaptation`, `script`, `characters`,
  `shot_table`, `image_prompts`, `video_prompts`, `sound_plan`, and
  `edit_plan`.
- CLI can render prompts and create requests with `manual_file`, `codex_web`,
  or opt-in `api_command` modes.
- Manual response queue exists with collect/apply flow.
- Collected output remains raw until `apply-output` promotes it.
- Structural validation exists for required files, JSON, CSV headers, row
  values, statuses, and cross-file shot references.
- `review` and `next` identify the next incomplete stage.
- Artifact application has backup and rollback behavior.
- Collected-output inspection and mechanical repair helpers exist.
- Asset naming conventions exist for storyboard, character reference, image,
  video, voice, music, SFX, subtitle, and export files.
- Draft edit plan builder and text manifest export exist.
- SRT/VTT subtitle export exists.
- Optional `ffmpeg` rough-cut command exists, with clear failure when `ffmpeg`
  or clip files are missing.
- Project pack/unpack exists for moving ignored generated work between
  machines.
- Request dashboard exists with pending/completed stage, mode, target site, and
  target model metadata.
- `doctor` exists for local readiness checks, with optional tiny OpenAI smoke
  testing when explicitly requested.
- Generated media can be imported into conventional asset folders and tracked
  in `asset_manifest.json`.
- Asset candidates can be selected or rejected, with selection updating
  `image_prompts.csv`, `video_prompts.csv`, `voice_lines.csv`,
  `sound_plan.csv`, matching `edit_plan.json` clips, or character references
  where possible.
- Missing referenced media can be reported before render/export.
- Tests cover the core CLI/project/queue/apply/bundle/subtitle/renderer
  preflight paths plus request metadata, asset import/selection, missing media,
  and diagnostics.

## Roadmap To Account-Ready Use

The remaining work should move in this order. Keep each step usable without API
keys unless the user explicitly requests an API wrapper.

The next milestone should be one real 60-90 second pilot run. Do not jump to a
generic UI or broad provider integrations before the project proves the
end-to-end loop with actual generated images, clips, voices, music/SFX,
subtitles, and a review cut.

### Phase 1: Real Pilot Hardening

Goal: prove the whole structured workflow on one short, using either an
original idea or source material the user has the rights to use.

- Add source-rights metadata and safety checks so adapted material, excerpts,
  uploads, and publishing rights are not treated casually.
- Extend asset selection so selecting one candidate can optionally mark sibling
  candidates for the same shot/line/cue as rejected or needs_review.
- Add richer review commands for visual continuity, character consistency,
  prompt completeness, audio coverage, and missing selected assets.
- Add continuity controls around character references, style-lock prompts,
  negative prompts, per-character reference-image lifecycle, and visual drift
  review.
- Add a shot-level generation loop: image candidates -> selected frame -> video
  prompt -> generated clips -> selected clip -> retry/repair decision.
- Run an end-to-end pilot through all stages using manual paste only.
- Update prompt templates based on the first pilot's failures, especially
  character consistency, shot simplicity, and video motion clarity.

### Phase 2: Codex Web Operator Playbooks

Goal: once the user is logged into required websites, Codex can operate the
workflow repeatably from pending request files.

- Add provider-neutral operator docs for text, image, image-to-video, voice,
  music, and SFX generation.
- Add target-site fields and run notes to requests in a way that works for
  browser automation, computer use, or manual paste.
- Add explicit upload safety prompts for copyrighted/private source material.
- Add per-provider playbooks only after the user chooses actual websites.
- Record what each website returns and where downloaded assets should be saved.
- Exercise at least one live text, image, video, and voice/music/SFX workflow
  with logged-in accounts before calling the project account-ready.
- Keep all website automation best-effort; a manual response file fallback must
  always remain available.

### Phase 3: Media Assembly

Goal: after generated assets exist locally, the project can produce a watchable
review cut.

- Strengthen `edit_plan.json` validation for clips, audio groups, subtitles,
  timing, transitions, and runtime.
- Improve `render-rough-cut` from concat-only behavior to robust `ffmpeg`
  rendering with re-encoding, scaling to 16:9, audio placement, subtitles, and
  loudness normalization.
- Add missing-media reports before rendering.
- Add sound implementation checks: line-to-audio mapping, voice duration,
  subtitle sync, music/SFX timing, ambience coverage, and loudness targets.
- Add export formats for human editors, such as CSV/EDL-style manifests and
  clear per-shot asset lists.
- Add final QA checks for duration, aspect ratio, missing captions, missing
  dialogue, missing music/SFX, and unresolved review statuses.
- Test a real rough cut with actual generated clips and audio for a complete
  60-90 second pilot.

### Phase 4: Local UI

Goal: make the workflow practical for repeated use without memorizing commands.

- Add a small local UI after the CLI is stable.
- First screen should be an operational dashboard, not a marketing page.
- Show current project, stage status, pending requests, paste targets, collected
  outputs, selected assets, and render/export actions.
- Keep all actions backed by the same CLI/file workflow so the UI does not
  become a separate system.

### Phase 5: Optional API Wrappers

Goal: allow automation for users who explicitly choose API spending.

- Keep `api_command` as the integration boundary.
- Add example local wrapper scripts only when the user asks for a specific
  provider.
- Never store API keys in committed files.
- Never make API mode the default.

## Ready-For-Use Definition

The project is "ready once accounts are logged in" when all of the following
are true:

- A user can create a project from an original idea or rights-cleared source.
- `mythoframe next <slug>` can drive every planning stage through request,
  collect, inspect, apply, and validate.
- A Codex agent can read pending requests and operate the chosen logged-in model
  websites using documented playbooks.
- At least one logged-in text, image, video, and sound/voice provider workflow
  has been tested end to end, even if the provider-specific automation remains
  partly manual.
- A manual paste fallback exists for every external generation step.
- Generated images, clips, voice, music, and SFX can be imported or registered
  into the project without hand-editing paths.
- Selected assets can be linked to prompts, shots, voice lines, sound cues, and
  edit clips.
- Candidate assets retain provenance, selected/rejected state, and retry notes.
- The project can export subtitles, an edit manifest, and a rough cut from local
  assets.
- The rough cut has been tested with real generated clips and audio, not only
  with preflight checks.
- The user can bundle the full local project and continue on another machine.
- Validation catches missing or malformed files before export.
- Review gates cover continuity, timing, sound coverage, and unresolved drafts;
  structural validation alone is not considered release-ready.
- No paid API call, upload, account creation, or purchase happens without an
  explicit user action.

## Account And Setup Dependencies

Do not hardcode these until the user chooses exact providers. Future agents
should ask the user which accounts they want to use, then write provider
playbooks around those choices.

Required or likely required:

- GitHub access for source control.
- Logged-in text model website for adaptation, script, planning, and prompt
  refinement.
- Logged-in image generation website for character references and storyboard
  frames.
- Logged-in image-to-video generation website for shot clips.
- Logged-in voice or dubbing website for dialogue and narration.
- Music and SFX source, either generated, licensed, or user-provided.
- Local `ffmpeg` for automated rough cuts, unless editing is done manually in an
  external editor.
- Enough local disk space for generated media and project bundles.

Optional later:

- API keys and wrappers for any provider the user explicitly wants to automate.
- Cloud storage for moving large generated assets.
- Social media accounts for publishing.
- Editing app integration for CapCut, Premiere Pro, DaVinci Resolve, or another
  editor.

## Provider Selection Guidance

Provider-specific work should wait until the user selects target accounts. When
adding one:

- Add docs first: login assumptions, upload/download steps, expected output
  files, naming convention, and known manual fallback.
- Add automation second: browser/computer-use instructions that operate pending
  request files.
- Add API wrappers last and only as opt-in examples.
- Verify current website terms, pricing, and content policies before relying on
  any provider-specific workflow.

## Current Risks

- Offline original pilot scaffolding exists, but no user-selected source project
  has been created yet.
- No book, manga, or user-owned story source has been selected.
- Rights/source handling is not yet implemented beyond human caution in docs.
- No provider web workflows have been tested against live model sites.
- Asset import/selection exists, but has only been tested with local dummy files,
  not actual downloaded provider outputs.
- Candidate tracking exists, but retry grouping and automatic sibling rejection
  are still basic.
- Character/style continuity is planned but not yet enforced by reference-image
  lifecycle, style-lock prompts, or review gates.
- Sound planning exists, but line-to-audio sync, music/SFX sourcing, subtitle
  sync, and loudness checks are not production-ready.
- Rough-cut rendering exists, but it has not been exercised with real generated
  clips in a production project.
- Asset naming conventions exist, but no real generated assets have been linked
  through a production project yet.
- Current validation is structural. It does not prove the short is coherent,
  emotionally timed, visually consistent, or publishable.
- Manual-first operation can become copy-paste heavy unless Codex web playbooks
  and asset ingestion become procedural.
- Web model workflows will be brittle because provider UIs change; the file
  queue is the mitigation, not a complete solution.
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
