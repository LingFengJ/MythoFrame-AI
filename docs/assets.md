# Asset Naming

Generated assets should be named so shot, version, and purpose are obvious.

Use the CLI helper to preview conventional paths:

```powershell
mythoframe asset-name pilot-scene storyboard --shot 1
mythoframe asset-name pilot-scene video_clip --shot 1
mythoframe asset-name pilot-scene voice --shot 1 --line 1
```

Conventions:

| Type | Pattern |
| --- | --- |
| Character reference | `assets/references/<character>_ref_v001.png` |
| Storyboard image | `assets/storyboards/shot_001_img_v001.png` |
| Video clip | `assets/video_clips/shot_001_clip_v001.mp4` |
| Voice line | `assets/audio/voice/shot_001_line_001_v001.wav` |
| Sound effect | `assets/audio/sfx/shot_001_<cue>_v001.wav` |
| Music | `assets/audio/music/<cue>_v001.wav` |
| Export | `assets/exports/<project>_rough_cut_v001.mp4` |

These are conventions, not generated media. The project should not commit large
generated assets by default.

Generated project assets live under `projects/*/assets/`, which is ignored by
Git. Track only small metadata, examples, or explicitly curated assets.

## Import And Select Generated Media

After downloading output from a model website, import it into the project:

```powershell
mythoframe import-asset pilot-scene storyboard .\downloads\shot1.png --shot 1 --candidate-id shot_001_a --provider "ImageSite"
mythoframe import-asset pilot-scene video_clip .\downloads\shot1.mp4 --shot 1 --candidate-id shot_001_clip_a --provider "VideoSite"
mythoframe import-asset pilot-scene voice .\downloads\line1.wav --shot 1 --line 1 --candidate-id line_001_voice_a --provider "VoiceSite"
mythoframe import-asset pilot-scene sfx .\downloads\wind.wav --shot 1 --cue wind --candidate-id wind_sfx_a
```

Each import copies the file into the conventional asset folder and records a
candidate in `asset_manifest.json` with provider, request id, notes, status,
and project-relative path.

Choose or reject a candidate:

```powershell
mythoframe select-asset pilot-scene shot_001_a
mythoframe select-asset pilot-scene shot_001_b --status rejected --notes "face drift"
```

Selection updates the manifest and the canonical consumption field when
possible:

| Asset type | Updated artifact |
| --- | --- |
| `storyboard` | `image_prompts.csv:selected_asset` |
| `video_clip` | `video_prompts.csv:selected_clip` and matching `edit_plan.json` clips |
| `voice` | `voice_lines.csv:audio_asset` |
| `sfx` / `music` | `sound_plan.csv:audio_asset` |
| `reference` | matching `characters.json:reference_assets` when a character can be matched |

Review candidates and missing paths:

```powershell
mythoframe assets pilot-scene
mythoframe assets pilot-scene --status selected
mythoframe missing-media pilot-scene
```
