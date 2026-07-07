"""Operational readiness checks."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from mythoframe.media import missing_media
from mythoframe.project import validate_project


@dataclass(frozen=True)
class DiagnosticCheck:
    name: str
    status: str
    detail: str


def run_doctor(
    root: Path,
    project_path: Path | None = None,
    *,
    openai_smoke: bool = False,
    openai_model: str = "gpt-4.1-mini",
    openai_max_output_tokens: int = 16,
) -> list[DiagnosticCheck]:
    checks = [
        _python_check(),
        _root_check(root),
        _writable_check(root),
        _ffmpeg_check(),
        _openai_key_check(),
    ]
    if project_path is not None:
        checks.extend(_project_checks(project_path))
    if openai_smoke:
        checks.append(_openai_smoke_check(openai_model, openai_max_output_tokens))
    return checks


def has_failures(checks: list[DiagnosticCheck]) -> bool:
    return any(check.status == "fail" for check in checks)


def _python_check() -> DiagnosticCheck:
    version = ".".join(str(part) for part in sys.version_info[:3])
    status = "ok" if sys.version_info >= (3, 10) else "fail"
    return DiagnosticCheck("python", status, f"{version} on {platform.system()}")


def _root_check(root: Path) -> DiagnosticCheck:
    required = ("pyproject.toml", "src", "prompts")
    missing = [name for name in required if not (root / name).exists()]
    if missing:
        return DiagnosticCheck("workspace", "fail", f"Missing: {', '.join(missing)}")
    return DiagnosticCheck("workspace", "ok", str(root))


def _writable_check(root: Path) -> DiagnosticCheck:
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=".mythoframe_doctor_", delete=True):
            pass
    except OSError as exc:
        return DiagnosticCheck("workspace_write", "fail", str(exc))
    return DiagnosticCheck("workspace_write", "ok", "workspace root is writable")


def _ffmpeg_check() -> DiagnosticCheck:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return DiagnosticCheck("ffmpeg", "ok", ffmpeg)
    return DiagnosticCheck("ffmpeg", "warn", "ffmpeg not found; rough-cut rendering will be unavailable")


def _openai_key_check() -> DiagnosticCheck:
    if os.environ.get("OPENAI_API_KEY"):
        return DiagnosticCheck("openai_key", "ok", "OPENAI_API_KEY is present")
    return DiagnosticCheck("openai_key", "warn", "OPENAI_API_KEY is not set")


def _project_checks(project_path: Path) -> list[DiagnosticCheck]:
    checks: list[DiagnosticCheck] = []
    problems = validate_project(project_path)
    if problems:
        checks.append(DiagnosticCheck("project_validation", "fail", f"{len(problems)} problem(s)"))
    else:
        checks.append(DiagnosticCheck("project_validation", "ok", str(project_path)))

    missing = missing_media(project_path)
    if missing:
        checks.append(DiagnosticCheck("missing_media", "fail", f"{len(missing)} missing referenced file(s)"))
    else:
        checks.append(DiagnosticCheck("missing_media", "ok", "no missing referenced media"))
    return checks


def _openai_smoke_check(model: str, max_output_tokens: int) -> DiagnosticCheck:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return DiagnosticCheck("openai_smoke", "fail", "OPENAI_API_KEY is not set")
    if max_output_tokens < 16 or max_output_tokens > 32:
        return DiagnosticCheck(
            "openai_smoke",
            "fail",
            "max output tokens must be between 16 and 32",
        )

    body = json.dumps(
        {
            "model": model,
            "input": "Reply with exactly: mythoframe-ok",
            "max_output_tokens": max_output_tokens,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        return DiagnosticCheck("openai_smoke", "fail", f"HTTP {exc.code}: {detail}")
    except OSError as exc:
        return DiagnosticCheck("openai_smoke", "fail", str(exc))

    output = _response_text(payload).strip().lower()
    if "mythoframe-ok" in output:
        return DiagnosticCheck("openai_smoke", "ok", f"{model} responded")
    return DiagnosticCheck("openai_smoke", "warn", "API responded, but smoke text was unexpected")


def _response_text(payload: dict[str, object]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str):
        return direct

    texts: list[str] = []
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    texts.append(text)
    return "\n".join(texts)
