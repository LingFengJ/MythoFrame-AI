"""Project bundle import/export helpers."""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mythoframe.project import project_dir, slugify, validate_project
from mythoframe.schemas import PROJECT_DIRS


BUNDLE_VERSION = 1


@dataclass(frozen=True)
class BundleResult:
    path: Path
    files: int


def pack_project(root: Path, slug: str, output_path: Path | None = None) -> BundleResult:
    source = project_dir(root, slug)
    if not source.exists():
        raise FileNotFoundError(f"Project does not exist: {source}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = output_path or (root / "bundles" / f"{slugify(slug)}_{stamp}.mythoframe.zip")
    output.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "bundle_version": BUNDLE_VERSION,
        "project_slug": slugify(slug),
        "created_utc": stamp,
    }

    count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
        count += 1
        for file_path in sorted(source.rglob("*")):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(source)
            archive.write(file_path, f"project/{relative.as_posix()}")
            count += 1

    return BundleResult(path=output, files=count)


def unpack_project(
    root: Path,
    bundle_path: Path,
    *,
    slug: str | None = None,
    force: bool = False,
) -> BundleResult:
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle does not exist: {bundle_path}")

    with zipfile.ZipFile(bundle_path, "r") as archive:
        manifest = _read_manifest(archive)
        target_slug = slugify(slug or str(manifest["project_slug"]))
        target = project_dir(root, target_slug)
        if target.exists():
            if not force:
                raise FileExistsError(f"Project already exists: {target}")
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

        count = 0
        for member in archive.infolist():
            if member.is_dir() or member.filename == "manifest.json":
                continue
            if not member.filename.startswith("project/"):
                continue
            relative = Path(member.filename.removeprefix("project/"))
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe bundle path: {member.filename}")
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as src, destination.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            count += 1

    for relative in PROJECT_DIRS:
        (target / relative).mkdir(parents=True, exist_ok=True)

    problems = validate_project(target)
    if problems:
        details = "\n".join(f"- {problem}" for problem in problems)
        raise ValueError(f"Unpacked project failed validation:\n{details}")
    return BundleResult(path=target, files=count)


def _read_manifest(archive: zipfile.ZipFile) -> dict[str, object]:
    try:
        raw = archive.read("manifest.json")
    except KeyError as exc:
        raise ValueError("Bundle is missing manifest.json") from exc
    manifest = json.loads(raw.decode("utf-8"))
    if manifest.get("bundle_version") != BUNDLE_VERSION:
        raise ValueError(f"Unsupported bundle version: {manifest.get('bundle_version')}")
    if not manifest.get("project_slug"):
        raise ValueError("Bundle manifest is missing project_slug")
    return manifest
