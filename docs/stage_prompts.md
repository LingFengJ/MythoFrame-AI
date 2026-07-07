# Stage Prompts

The prompt layer is file-based and editable. Templates live in
`prompts/stages/`.

Supported stages:

- `adaptation`
- `script`
- `characters`
- `shot_table`
- `image_prompts`
- `video_prompts`
- `sound_plan`
- `edit_plan`

Render a prompt without creating a request:

```powershell
mythoframe prompt pilot-scene script
```

Write a rendered prompt to a file:

```powershell
mythoframe prompt pilot-scene script --out scratch/script_prompt.md
```

Create a manual request from a stage template:

```powershell
mythoframe request-stage pilot-scene script
```

Create a Codex-assisted web request:

```powershell
mythoframe request-stage pilot-scene script --mode codex_web --target-site ChatGPT
```

The rendered prompt is built from project files such as `project_bible.json`,
`source_brief.md`, `adaptation.md`, `script.md`, `characters.json`, and the CSV
planning files.

