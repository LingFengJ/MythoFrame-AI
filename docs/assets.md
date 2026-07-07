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
