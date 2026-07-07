from __future__ import annotations

import sys
import shutil
import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mythoframe.assets import asset_path
from mythoframe.artifacts import apply_stage_output
from mythoframe.bundle import pack_project, unpack_project
from mythoframe.manual_queue import collect_response, create_request, is_ready
from mythoframe.cli import main
from mythoframe.output_tools import inspect_stage_output, repair_stage_output
from mythoframe.pilot import init_pilot_project
from mythoframe.prompts import render_stage_prompt
from mythoframe.project import ProjectSpec, init_project, project_dir, validate_project
from mythoframe.renderer import render_rough_cut
from mythoframe.schemas import OUTPUT_MARKER
from mythoframe.subtitles import export_subtitles
from mythoframe.workflow import next_stage, stage_statuses


class BackboneTests(TestCase):
    def test_init_project_creates_required_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")

            self.assertTrue((path / "source_brief.md").exists())
            self.assertTrue((path / "adaptation.md").exists())
            self.assertTrue((path / "project_bible.json").exists())
            self.assertTrue((path / "shot_table.csv").exists())
            self.assertEqual(validate_project(path), [])

    def test_manual_request_collects_response(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")

            record = create_request(path, "script", "Write a test script.")
            self.assertFalse(is_ready(record.response_path))

            record.response_path.write_text(
                f"Header\n{OUTPUT_MARKER}\nGenerated script.",
                encoding="utf-8",
            )
            self.assertTrue(is_ready(record.response_path))

            output = collect_response(path, record.request_id)
            self.assertEqual(output.read_text(encoding="utf-8").strip(), "Generated script.")
            self.assertFalse(record.response_path.exists())
            self.assertTrue((path / "requests" / "completed" / record.response_path.name).exists())

    def test_cli_init_and_validate(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(
                main(["--root", tmp, "init", "pilot", "--title", "Pilot"]),
                0,
            )
            self.assertEqual(main(["--root", tmp, "validate", "pilot"]), 0)

    def test_stage_prompt_renders_project_context(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(__file__).resolve().parents[1]
            project_root = Path(tmp)
            init_project(project_root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(project_root, "pilot")

            prompt = render_stage_prompt(root, path, "script")

            self.assertIn("MythoFrame Stage Prompt: Script", prompt)
            self.assertIn("Pilot Source Brief", prompt)
            self.assertIn("60-90 second", prompt)

    def test_cli_request_stage_creates_metadata_request(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(__file__).resolve().parents[1]
            root = Path(tmp)
            shutil.copytree(repo_root / "prompts", root / "prompts")
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))

            self.assertEqual(
                main(
                    [
                        "--root",
                        tmp,
                        "request-stage",
                        "pilot",
                        "script",
                        "--target-site",
                        "ChatGPT",
                    ]
                ),
                0,
            )

            pending = project_dir(root, "pilot") / "requests" / "pending"
            request_files = list(pending.glob("*.request.md"))
            self.assertEqual(len(request_files), 1)
            request_text = request_files[0].read_text(encoding="utf-8")
            self.assertIn("- Target Site: ChatGPT", request_text)
            self.assertIn("- Expected Format: markdown", request_text)
            self.assertIn("- Cost Policy: manual_file/codex_web by default", request_text)
            self.assertIn("## Acceptance Checklist", request_text)
            self.assertIn("MythoFrame Stage Prompt: Script", request_text)

    def test_validation_rejects_bad_csv_header(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            (path / "shot_table.csv").write_text("bad,header\n", encoding="utf-8")

            problems = validate_project(path)

            self.assertTrue(any("Unexpected CSV headers" in problem for problem in problems))

    def test_validation_rejects_bad_csv_row_values(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            (path / "shot_table.csv").write_text(
                (
                    "shot_number,duration,camera_movement,framing,visual_description,"
                    "image_prompt,video_prompt,dialogue,narration,music,sound_effects,"
                    "review_status\n"
                    "one,three seconds,pan,wide,scene,img,vid,,,,,done\n"
                ),
                encoding="utf-8",
            )

            problems = validate_project(path)

            self.assertTrue(any("Expected integer `shot_number`" in problem for problem in problems))
            self.assertTrue(any("Expected duration like" in problem for problem in problems))
            self.assertTrue(any("Invalid `review_status`" in problem for problem in problems))

    def test_validation_rejects_unknown_shot_reference(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            (path / "shot_table.csv").write_text(
                (
                    "shot_number,duration,camera_movement,framing,visual_description,"
                    "image_prompt,video_prompt,dialogue,narration,music,sound_effects,"
                    "review_status\n"
                    "1,3s,pan,wide,scene,img,vid,,,,,draft\n"
                ),
                encoding="utf-8",
            )
            (path / "image_prompts.csv").write_text(
                (
                    "shot_number,candidate_id,prompt,reference_assets,negative_prompt,status,"
                    "selected_asset\n"
                    "2,shot_002_a,prompt,pending_reference,,draft,\n"
                ),
                encoding="utf-8",
            )

            problems = validate_project(path)

            self.assertTrue(any("Unknown shot_number" in problem for problem in problems))

    def test_asset_path_convention(self) -> None:
        with TemporaryDirectory() as tmp:
            project = Path(tmp) / "projects" / "pilot"

            self.assertEqual(
                asset_path(project, "storyboard", shot=1).as_posix(),
                (project / "assets" / "storyboards" / "shot_001_img_v001.png").as_posix(),
            )
            self.assertEqual(
                asset_path(project, "voice", shot=2, line=3).as_posix(),
                (
                    project
                    / "assets"
                    / "audio"
                    / "voice"
                    / "shot_002_line_003_v001.wav"
                ).as_posix(),
            )

    def test_pilot_scaffold_writes_original_source_brief(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = init_pilot_project(root)

            source = (path / "source_brief.md").read_text(encoding="utf-8")
            bible = json.loads((path / "project_bible.json").read_text(encoding="utf-8"))

            self.assertIn("The Last Lantern", source)
            self.assertEqual(bible["project"]["status"], "pilot_seeded")
            self.assertEqual(validate_project(path), [])

    def test_workflow_status_finds_next_stage(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = init_pilot_project(root)

            statuses = stage_statuses(path)
            next_status = next_stage(path)

            self.assertEqual(statuses[0].stage, "adaptation")
            self.assertEqual(next_status.stage, "adaptation")
            self.assertEqual(next_status.status, "draft")

    def test_cli_pilot_and_review(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(main(["--root", tmp, "pilot", "pilot-scene"]), 0)
            self.assertEqual(main(["--root", tmp, "review", "pilot-scene"]), 0)

    def test_apply_markdown_output_updates_script(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            output_dir = path / "outputs" / "script"
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "001.md"
            output.write_text("```markdown\n# Pilot Script\n\nScene text.\n```", encoding="utf-8")

            result = apply_stage_output(path, "script", output)

            self.assertEqual(result.written_files, (path / "script.md",))
            self.assertEqual((path / "script.md").read_text(encoding="utf-8").strip(), "# Pilot Script\n\nScene text.")

    def test_apply_json_output_normalizes_characters(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            output_dir = path / "outputs" / "characters"
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "001.md"
            output.write_text(
                (
                    "```json\n"
                    '{"characters":[{"id":"courier","name":"Courier",'
                    '"reference_prompt":"ref","consistency_prompt":"same"}],'
                    '"consistency_rules":[]}'
                    "\n```"
                ),
                encoding="utf-8",
            )

            apply_stage_output(path, "characters", output)
            data = json.loads((path / "characters.json").read_text(encoding="utf-8"))

            self.assertEqual(data["characters"][0]["id"], "courier")
            self.assertEqual(validate_project(path), [])

    def test_apply_sound_plan_splits_two_csv_blocks(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            (path / "shot_table.csv").write_text(
                (
                    "shot_number,duration,camera_movement,framing,visual_description,"
                    "image_prompt,video_prompt,dialogue,narration,music,sound_effects,"
                    "review_status\n"
                    "1,3s,pan,wide,scene,img,vid,Hello,,soft,wind,draft\n"
                ),
                encoding="utf-8",
            )
            output_dir = path / "outputs" / "sound_plan"
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "001.md"
            output.write_text(
                (
                    "```csv\n"
                    "line_id,shot_number,speaker,text,voice_style,status,audio_asset\n"
                    "1,1,Courier,Hello,warm,draft,assets/audio/voice/shot_001_line_001_v001.wav\n"
                    "```\n\n"
                    "```csv\n"
                    "cue_id,shot_number,cue_type,description,timing,status,audio_asset\n"
                    "wind,1,sfx,Wind through stone,whole shot,draft,assets/audio/sfx/shot_001_wind_v001.wav\n"
                    "```"
                ),
                encoding="utf-8",
            )

            apply_stage_output(path, "sound_plan", output)

            self.assertIn("Courier", (path / "voice_lines.csv").read_text(encoding="utf-8"))
            self.assertIn("Wind through stone", (path / "sound_plan.csv").read_text(encoding="utf-8"))
            self.assertEqual(validate_project(path), [])

    def test_apply_invalid_output_rolls_back(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            original = (path / "characters.json").read_text(encoding="utf-8")
            output_dir = path / "outputs" / "characters"
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "001.md"
            output.write_text('{"characters":"not a list"}', encoding="utf-8")

            with self.assertRaises(ValueError):
                apply_stage_output(path, "characters", output)

            self.assertEqual((path / "characters.json").read_text(encoding="utf-8"), original)

    def test_cli_apply_output_and_draft_edit_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            output_dir = path / "outputs" / "shot_table"
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "001.md"
            output.write_text(
                (
                    "```csv\n"
                    "shot_number,duration,camera_movement,framing,visual_description,"
                    "image_prompt,video_prompt,dialogue,narration,music,sound_effects,"
                    "review_status\n"
                    "1,3s,pan,wide,scene,img,vid,,,,,draft\n"
                    "```"
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                main(["--root", tmp, "apply-output", "pilot", "shot_table"]),
                0,
            )
            self.assertEqual(main(["--root", tmp, "draft-edit", "pilot"]), 0)
            self.assertEqual(main(["--root", tmp, "export-manifest", "pilot"]), 0)
            manifest = path / "assets" / "exports" / "edit_manifest.txt"

            self.assertTrue(manifest.exists())
            self.assertIn("shot 1", manifest.read_text(encoding="utf-8"))

    def test_pack_unpack_round_trip_includes_ignored_work(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = init_pilot_project(root)
            ignored_output = path / "outputs" / "script" / "raw.md"
            ignored_output.parent.mkdir(parents=True, exist_ok=True)
            ignored_output.write_text("raw output", encoding="utf-8")

            bundle = pack_project(root, "pilot-scene").path
            with zipfile.ZipFile(bundle) as archive:
                self.assertIn("project/outputs/script/raw.md", archive.namelist())

            new_root = root / "other"
            result = unpack_project(new_root, bundle)

            self.assertTrue((result.path / "source_brief.md").exists())
            self.assertEqual((result.path / "outputs" / "script" / "raw.md").read_text(encoding="utf-8"), "raw output")

    def test_output_inspect_and_repair(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            output_dir = path / "outputs" / "characters"
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "001.md"
            output.write_text(
                (
                    "Here is the JSON:\n"
                    "```json\n"
                    '{"characters":[{"id":"hero","name":"Hero",'
                    '"reference_prompt":"ref","consistency_prompt":"same"}],'
                    '"consistency_rules":[]}'
                    "\n```"
                ),
                encoding="utf-8",
            )

            inspection = inspect_stage_output(path, "characters", output)
            repaired = repair_stage_output(path, "characters", output)

            self.assertTrue(inspection.parse_ok)
            self.assertIn("Parsed artifacts", inspection.messages[0])
            self.assertIn("characters.json", repaired.read_text(encoding="utf-8"))

    def test_subtitle_export_from_voice_lines(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            (path / "shot_table.csv").write_text(
                (
                    "shot_number,duration,camera_movement,framing,visual_description,"
                    "image_prompt,video_prompt,dialogue,narration,music,sound_effects,"
                    "review_status\n"
                    "1,2.5s,pan,wide,scene,img,vid,Hello,,soft,wind,draft\n"
                ),
                encoding="utf-8",
            )
            (path / "voice_lines.csv").write_text(
                (
                    "line_id,shot_number,speaker,text,voice_style,status,audio_asset\n"
                    "1,1,Courier,Hello there,warm,draft,\n"
                ),
                encoding="utf-8",
            )

            srt = export_subtitles(path, fmt="srt")
            vtt = export_subtitles(path, fmt="vtt")

            self.assertIn("00:00:00,000 --> 00:00:02,500", srt.read_text(encoding="utf-8"))
            self.assertTrue(vtt.read_text(encoding="utf-8").startswith("WEBVTT"))

    def test_rough_cut_requires_ffmpeg(self) -> None:
        with patch("mythoframe.renderer.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "ffmpeg"):
                render_rough_cut(Path("unused"))

    def test_rough_cut_reports_missing_assets_before_rendering(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")
            (path / "edit_plan.json").write_text(
                json.dumps({"clips": [{"video_asset": "assets/video_clips/missing.mp4"}]}),
                encoding="utf-8",
            )

            with patch("mythoframe.renderer.shutil.which", return_value="ffmpeg"):
                with self.assertRaisesRegex(FileNotFoundError, "Missing video assets"):
                    render_rough_cut(path)

    def test_cli_next_creates_request_for_next_stage(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_root = Path(__file__).resolve().parents[1]
            root = Path(tmp)
            shutil.copytree(repo_root / "prompts", root / "prompts")
            init_pilot_project(root)

            self.assertEqual(main(["--root", tmp, "next", "pilot-scene"]), 0)

            pending = project_dir(root, "pilot-scene") / "requests" / "pending"
            request_files = list(pending.glob("*.request.md"))
            self.assertEqual(len(request_files), 1)
            self.assertIn("- Stage: adaptation", request_files[0].read_text(encoding="utf-8"))

    def test_cli_pack_unpack_and_subtitles(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(main(["--root", tmp, "pilot", "pilot-scene"]), 0)
            self.assertEqual(main(["--root", tmp, "pack", "pilot-scene"]), 0)
            bundles = list((Path(tmp) / "bundles").glob("*.mythoframe.zip"))
            self.assertEqual(len(bundles), 1)

            unpack_root = Path(tmp) / "unpacked"
            self.assertEqual(
                main(["--root", str(unpack_root), "unpack", str(bundles[0])]),
                0,
            )
            self.assertTrue((unpack_root / "projects" / "pilot-scene").exists())
