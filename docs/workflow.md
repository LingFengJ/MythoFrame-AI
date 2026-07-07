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
