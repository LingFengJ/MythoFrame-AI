# Generation Modes

MythoFrame is built to avoid accidental paid model calls.

## Main Production Path

The CLI default is `manual_file` for safety, but the main production path when
Codex is actively helping is `codex_web`.

For video generation, this means:

1. MythoFrame creates a provider-ready request.
2. Codex opens the chosen web provider, currently Dreamina/CapCut first for
   Seedance video.
3. Codex uses browser automation when the page can be controlled directly.
4. Codex uses computer-use automation only when browser automation is not enough.
5. If automation is blocked by login, captcha, payment, changing UI, or site
   reliability, the user manually pastes the prompt/downloads the result.
6. The generated asset is imported into MythoFrame with `import-asset`, reviewed,
   selected or rejected, and then used by the local edit/export flow.

So the project is not pure manual copy/paste, and it is not "computer use every
time." It is Codex-orchestrated web generation with a durable manual fallback.

## `manual_file` Default

This is the default mode.

Use this when the user wants maximum control, when no logged-in model website is
available to Codex, or when the website blocks automation.

The CLI writes two files under `projects/<slug>/requests/pending/`:

- `<id>.request.md`
- `<id>.response.md`

The request file contains the prompt. The response file contains a marker. Paste
the model output below the marker, then run:

```powershell
python -m mythoframe --root . collect <slug>
```

The collected result is written to `projects/<slug>/outputs/<stage>/`.

For stage-specific prompts, prefer:

```powershell
mythoframe request-stage <slug> <stage>
```

For day-to-day production, the shortcut is:

```powershell
mythoframe next <slug>
```

It chooses the next incomplete stage and creates a default `manual_file`
request.

## `codex_web`

This mode is still file-based, but the request is written for a Codex operator.
Use this as the normal production mode when the user has asked Codex to operate
logged-in web tools.

Intended flow:

1. Run `mythoframe request-stage <slug> <stage> --mode codex_web`.
2. Ask Codex to process the pending request.
3. Codex uses browser use for model websites when possible.
4. Codex uses computer use for desktop/web UI fallback when needed.
5. If neither route works, the user manually pastes the result or downloads the
   generated media.
6. Run `mythoframe collect <slug>`.

The local project does not directly control Codex tools. It creates a durable
handoff queue that Codex can operate against.

Before promoting any web-generated output into project truth, run:

```powershell
mythoframe inspect-output <slug> <stage>
mythoframe apply-output <slug> <stage>
```

Use `repair-output` first if the web model added useful but messy wrapper text.

## `api_command`

This is the opt-in automation mode.

Set `MYTHOFRAME_API_COMMAND` to a local wrapper command. The wrapper receives:

1. Prompt file path
2. Output file path

Example wrapper contract:

```text
my-api-wrapper.exe C:\path\to\prompt.md C:\path\to\output.md
```

The wrapper can call OpenAI, Anthropic, Gemini, a local model, or any other
provider. MythoFrame does not make this mode default because model calls can be
expensive.
