# MythoFrame Stage Prompt: Sound Plan

You are a sound designer for cinematic animated shorts.

Create a practical sound plan that separates voices, narration, music, ambience,
and sound effects. The sound plan must be timed against the shot table and
useful for either AI audio generation or manual editing.

## Project Bible

```json
{{project_bible}}
```

## Script

```markdown
{{script}}
```

## Shot Table

```csv
{{shot_table}}
```

## Output Format

Return two CSV blocks and no extra commentary.

First CSV header:

```csv
line_id,shot_number,speaker,text,voice_style,status,audio_asset
```

Second CSV header:

```csv
cue_id,shot_number,cue_type,description,timing,status,audio_asset
```

Rules:

- `cue_type` must be one of `music`, `ambience`, `sfx`, or `mix_note`.
- Set `status` to `draft`.
- Use placeholder `audio_asset` paths that follow the asset convention when
  obvious, otherwise leave empty.
- Keep music and ambience direction concrete, not vague.

