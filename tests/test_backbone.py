from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mythoframe.manual_queue import collect_response, create_request, is_ready
from mythoframe.cli import main
from mythoframe.project import ProjectSpec, init_project, project_dir, validate_project
from mythoframe.schemas import OUTPUT_MARKER


class BackboneTests(TestCase):
    def test_init_project_creates_required_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_project(root, ProjectSpec(slug="pilot", title="Pilot"))
            path = project_dir(root, "pilot")

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
