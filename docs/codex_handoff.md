# Codex Handoff

Use this document when asking Codex to generate a MythoFrame artifact without
using paid API calls from the project itself.

## Main Path

The intended path is Codex-orchestrated web generation with manual fallback.

Codex should not treat every provider step as pure manual copy/paste. If the
user is logged in and the chosen web tool is usable from the current machine,
Codex should try to operate it. For Dreamina/Seedance video work, that means
opening the provider, pasting the prepared prompt, uploading references when
available, starting generation after user-approved paid actions, downloading the
result, and importing it back into MythoFrame.

Codex should also not jump directly to computer-use automation every time.
Prefer browser automation for browser pages. Use computer use only when browser
automation cannot handle the provider UI. If either route is blocked by login,
captcha, payment confirmation, phone verification, site UI changes, or
unreliable controls, leave the request/response files ready for manual
paste/download.

## Operator Role

Codex should act as the model-web operator for pending requests:

1. Inspect `projects/<slug>/requests/pending/`.
2. Open the relevant `.request.md`.
3. Read the request metadata and acceptance checklist.
4. Use the user's chosen model web app if available.
5. Prefer browser automation when the target is a browser page.
6. Use computer-use automation only when browser automation is not suitable.
7. Paste the model result into the matching `.response.md` below the marker.
8. Run `mythoframe collect <slug>` or tell the user the response is ready.
9. Run `mythoframe inspect-output <slug> <stage>` for structured stages.
10. Use `mythoframe repair-output <slug> <stage>` when the model returned
    parseable content wrapped in extra explanation.
11. Run `mythoframe apply-output <slug> <stage>` when the user wants to promote
    the collected or repaired result into canonical project files.
12. Run `mythoframe validate <slug>` before treating collected output as
    project truth when the output is JSON or CSV.

## Safety Rules

- Do not paste API keys into model websites or response files.
- Do not upload copyrighted source material to third-party tools unless the user
  confirms the rights and destination.
- Do not submit purchases, subscriptions, account creation, or paid generation
  without explicit approval.
- Keep model outputs separated from verified project truth until reviewed.
- Treat `api_command` as opt-in only. Do not convert a web/manual request into a
  paid API call without explicit user approval.

## Fallback

If browser/computer automation cannot complete a request, leave the response
file in place. The user can paste the model result manually and then run:

```powershell
mythoframe collect <slug>
mythoframe inspect-output <slug> <stage>
```

## Routine Operation

When the user asks Codex to continue a project, start with:

```powershell
mythoframe review <slug>
mythoframe next <slug>
```

`next` creates the next stage request with the default manual-file path unless a
different mode is explicitly requested.
