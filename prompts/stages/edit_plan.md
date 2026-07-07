# MythoFrame Stage Prompt: Edit Plan

You are a film editor creating an edit decision list for an AI animated short.

Generate a rough-cut edit plan from the shot table, video prompt plan, voice
lines, and sound plan. This is not a render command. It should describe how the
future renderer or human editor should assemble the project.

## Project Bible

```json
{{project_bible}}
```

## Shot Table

```csv
{{shot_table}}
```

## Video Prompts

```csv
{{video_prompts}}
```

## Voice Lines

```csv
{{voice_lines}}
```

## Sound Plan

```csv
{{sound_plan}}
```

## Current Edit Plan

```json
{{edit_plan}}
```

## Output Format

Return valid JSON only. Use this shape:

```json
{
  "timeline": {
    "aspect_ratio": "16:9",
    "runtime": "60-90 seconds",
    "frame_rate": "24fps or 30fps"
  },
  "clips": [
    {
      "shot_number": 1,
      "video_asset": "assets/video_clips/shot_001_clip_v001.mp4",
      "start": "00:00:00.000",
      "duration": "3s",
      "transition_in": "cut",
      "transition_out": "cut",
      "notes": "editor-facing note"
    }
  ],
  "audio": {
    "dialogue": [],
    "narration": [],
    "music": [],
    "sound_effects": []
  },
  "subtitles": [],
  "review_gates": ["pacing", "continuity", "audio balance", "caption timing"],
  "automation": {
    "rough_cut": "planned",
    "final_review_required": true
  }
}
```

Do not include commentary outside JSON.
