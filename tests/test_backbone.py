from __future__ import annotations

import sys
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mythoframe.assets import asset_path
from mythoframe.manual_queue import collect_response, create_request, is_ready
from mythoframe.cli import main
from mythoframe.prompts import render_stage_prompt
from mythoframe.project import ProjectSpec, init_project, project_dir, validate_project
from mythoframe.schemas import OUTPUT_MARKER


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
