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
mythoframe validate pilot-scene
```

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

