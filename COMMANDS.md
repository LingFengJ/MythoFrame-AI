# MythoFrame Commands

This is the short cheat sheet. Use `mythoframe guide` for the same workflow from
the CLI.

## Planning Loop

```powershell
mythoframe pilot pilot-scene
mythoframe review pilot-scene
mythoframe next pilot-scene
mythoframe collect pilot-scene
mythoframe inspect-output pilot-scene <stage>
mythoframe apply-output pilot-scene <stage>
mythoframe validate pilot-scene
```

`next` and `request-stage` default to the `seedance-first` provider profile.
Override with `--target-site`, `--target-model`, or `--operator-notes` only when
needed.

Repeat the loop through:

```text
adaptation -> script -> characters -> shot_table -> image_prompts -> video_prompts -> sound_plan -> edit_plan
```

## Seedance-First Media Loop

Use Seedance through Dreamina/CapCut first for video and native clip audio when
possible. Use Runway as the reliable fallback and seedance2.ai only as a cheap
unofficial candidate after testing. Use one image tool: ChatGPT Images,
Gemini/Nano Banana, or Seedream.

```powershell
mythoframe import-asset pilot-scene storyboard .\downloads\shot1.png --shot 1 --candidate-id shot_001_a --provider "ChatGPT Images"
mythoframe select-asset pilot-scene shot_001_a

mythoframe import-asset pilot-scene video_clip .\downloads\shot1.mp4 --shot 1 --candidate-id shot_001_clip_a --provider "Dreamina Seedance 2.0"
mythoframe select-asset pilot-scene shot_001_clip_a

mythoframe assets pilot-scene
mythoframe missing-media pilot-scene
```

## Editing And Export

```powershell
mythoframe draft-edit pilot-scene
mythoframe subtitles pilot-scene --format srt
mythoframe export-manifest pilot-scene
mythoframe render-rough-cut pilot-scene
mythoframe pack pilot-scene
```

## Status And Setup

```powershell
mythoframe requests pilot-scene --completed
mythoframe doctor pilot-scene
mythoframe providers
```
