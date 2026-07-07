# Codex Handoff

Use this document when asking Codex to generate a MythoFrame artifact without
using paid API calls from the project itself.

## Operator Role

Codex should act as the model-web operator for pending requests:

1. Inspect `projects/<slug>/requests/pending/`.
2. Open the relevant `.request.md`.
3. Use the user's chosen model web app if available.
4. Prefer browser automation when the target is a browser page.
5. Use computer-use automation only when browser automation is not suitable.
6. Paste the model result into the matching `.response.md` below the marker.
7. Run `mythoframe collect <slug>` or tell the user the response is ready.

## Safety Rules

- Do not paste API keys into model websites or response files.
- Do not upload copyrighted source material to third-party tools unless the user
  confirms the rights and destination.
- Do not submit purchases, subscriptions, account creation, or paid generation
  without explicit approval.
- Keep model outputs separated from verified project truth until reviewed.

## Fallback

If browser/computer automation cannot complete a request, leave the response
file in place. The user can paste the model result manually and then run:

```powershell
python -m mythoframe --root . collect <slug>
```

