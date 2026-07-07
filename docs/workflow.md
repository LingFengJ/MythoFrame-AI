# Workflow Commands

MythoFrame can be used without any API keys or website accounts.

## Create A Pilot

Create an original local pilot project for testing:

```powershell
mythoframe pilot pilot-scene
```

This writes a project under `projects/pilot-scene/`. Generated project folders
are ignored by Git by default, so pilot work stays local unless deliberately
exported or tracked.

## Work Through Stages

The default offline loop is:

```powershell
mythoframe review pilot-scene
mythoframe request-stage pilot-scene adaptation
mythoframe collect pilot-scene
mythoframe apply-output pilot-scene adaptation
mythoframe validate pilot-scene
```

`collect` preserves raw model output in `projects/<slug>/outputs/<stage>/`.
`apply-output` parses the latest collected output for that stage, writes the
canonical project artifact, and validates the project. If validation fails, the
canonical files are rolled back unless `--keep-invalid` is used.

Use `review` after each collection to see the next incomplete stage:

```powershell
mythoframe review pilot-scene
```

Or create a request for that next incomplete stage directly:

```powershell
mythoframe next pilot-scene
```

`next` uses the same stage prompt machinery as `request-stage`; it just asks the
workflow status helper which stage should be handled first.

## Inspect And Repair Collected Output

Before applying collected model output to canonical project files, inspect it:

```powershell
mythoframe inspect-output pilot-scene script
```

If the content is parseable but wrapped in extra explanation, normalize it into
a clean artifact block:

```powershell
mythoframe repair-output pilot-scene script
```

The repair command writes a sibling `.repaired.md` file beside the collected raw
output. Review that file, then pass it to `apply-output` when appropriate:

```powershell
mythoframe apply-output pilot-scene script --output-file projects/pilot-scene/outputs/script/<id>.repaired.md
```

## Validation

`validate` checks:

- Required project files and directories
- JSON structure for `project_bible.json`, `characters.json`, and `edit_plan.json`
- CSV headers and row-level required fields
- Numeric shot and line identifiers
- Status values
- Shot references across prompt, sound, and voice CSV files

Validation does not judge artistic quality. It catches structural problems
before generated output becomes project truth.

## Edit Plan Helpers

After shot, video, voice, and sound CSVs are populated, build a local draft edit
decision list without rendering media:

```powershell
mythoframe draft-edit pilot-scene
```

Export a text manifest for a human editor:

```powershell
mythoframe export-manifest pilot-scene
```

Export subtitles from `edit_plan.json` subtitles when available, or from
`voice_lines.csv` plus shot timing otherwise:

```powershell
mythoframe subtitles pilot-scene --format srt
mythoframe subtitles pilot-scene --format vtt
```

Render a local rough cut only when `ffmpeg` is installed and every clip in
`edit_plan.json` points to an existing local video file:

```powershell
mythoframe render-rough-cut pilot-scene
```

The rough cut is intentionally basic. It concatenates already-rendered clips for
review; final emotional pacing, continuity fixes, sound mix, and polish still
need human review.

## Move Work Between Machines

Generated projects, request queues, outputs, and media assets are ignored by Git
by default. Use a bundle when you need to continue a local project on another
machine:

```powershell
mythoframe pack pilot-scene
```

This writes a `.mythoframe.zip` under `bundles/` unless `--out` is provided.
Unpack it into another clone or workspace:

```powershell
mythoframe unpack bundles/pilot-scene_YYYYMMDDTHHMMSSZ.mythoframe.zip
```

Use `--slug` to rename the imported project, or `--force` to replace an
existing local project with the same slug.
