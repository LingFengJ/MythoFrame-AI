"""Command line interface for MythoFrame."""

from __future__ import annotations

import argparse
from pathlib import Path

from mythoframe.assets import ASSET_TYPES, asset_path
from mythoframe.manual_queue import (
    collect_response,
    create_request,
    is_ready,
    list_pending,
    wait_for_response,
)
from mythoframe.prompts import get_stage_spec, list_stage_specs, render_stage_prompt
from mythoframe.project import ProjectSpec, init_project, project_dir, validate_project
from mythoframe.pilot import init_pilot_project
from mythoframe.providers import ApiCommandProvider
from mythoframe.schemas import GENERATION_MODES, STAGE_NAMES
from mythoframe.workflow import next_stage, pending_request_summary, stage_statuses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mythoframe",
        description="Manual-first AI production workflow for animated shorts.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository or workspace root. Defaults to the current directory.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a project skeleton.")
    init_parser.add_argument("slug", help="Project slug, for example pilot-scene.")
    init_parser.add_argument("--title", required=True, help="Human-readable project title.")
    init_parser.add_argument("--aspect-ratio", default="16:9")
    init_parser.add_argument("--runtime", default="60-90 seconds")
    init_parser.add_argument("--source-type", default="to_be_determined")
    init_parser.add_argument("--force", action="store_true", help="Overwrite template files.")

    pilot_parser = subparsers.add_parser("pilot", help="Create an offline original pilot project.")
    pilot_parser.add_argument("slug", nargs="?", default="pilot-scene")
    pilot_parser.add_argument("--force", action="store_true", help="Overwrite seeded pilot files.")

    request_parser = subparsers.add_parser(
        "request",
        help="Create a generation request or run an opt-in API command provider.",
    )
    request_parser.add_argument("slug", help="Project slug.")
    request_parser.add_argument("stage", help="Stage name, for example script or characters.")
    request_parser.add_argument(
        "--mode",
        choices=GENERATION_MODES,
        default="manual_file",
        help="Generation mode. Defaults to manual_file.",
    )
    request_parser.add_argument("--prompt", help="Inline prompt text.")
    request_parser.add_argument("--prompt-file", help="Path to a prompt file.")
    request_parser.add_argument("--wait", action="store_true", help="Wait for manual response.")
    request_parser.add_argument("--poll-seconds", type=float, default=10.0)
    request_parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=0.0,
        help="Manual wait timeout. 0 means no timeout.",
    )
    _add_request_metadata_args(request_parser)

    stages_parser = subparsers.add_parser("stages", help="List supported workflow stages.")
    stages_parser.add_argument("--verbose", action="store_true")

    prompt_parser = subparsers.add_parser("prompt", help="Render a stage prompt.")
    prompt_parser.add_argument("slug", help="Project slug.")
    prompt_parser.add_argument("stage", choices=STAGE_NAMES, help="Workflow stage.")
    prompt_parser.add_argument("--source-file", help="Optional source brief path.")
    prompt_parser.add_argument("--out", help="Optional file to write the rendered prompt.")

    stage_request_parser = subparsers.add_parser(
        "request-stage",
        help="Render a stage prompt and create a generation request.",
    )
    stage_request_parser.add_argument("slug", help="Project slug.")
    stage_request_parser.add_argument("stage", choices=STAGE_NAMES, help="Workflow stage.")
    stage_request_parser.add_argument("--source-file", help="Optional source brief path.")
    stage_request_parser.add_argument(
        "--mode",
        choices=GENERATION_MODES,
        default="manual_file",
        help="Generation mode. Defaults to manual_file.",
    )
    stage_request_parser.add_argument("--wait", action="store_true", help="Wait for manual response.")
    stage_request_parser.add_argument("--poll-seconds", type=float, default=10.0)
    stage_request_parser.add_argument("--timeout-seconds", type=float, default=0.0)
    _add_request_metadata_args(stage_request_parser)

    status_parser = subparsers.add_parser("status", help="Show pending generation requests.")
    status_parser.add_argument("slug", help="Project slug.")

    collect_parser = subparsers.add_parser("collect", help="Collect ready response files.")
    collect_parser.add_argument("slug", help="Project slug.")
    collect_parser.add_argument("--request-id", help="Collect one request id only.")

    validate_parser = subparsers.add_parser("validate", help="Validate project structure.")
    validate_parser.add_argument("slug", help="Project slug.")

    review_parser = subparsers.add_parser("review", help="Summarize project workflow status.")
    review_parser.add_argument("slug", help="Project slug.")

    asset_parser = subparsers.add_parser("asset-name", help="Print a conventional asset path.")
    asset_parser.add_argument("slug", help="Project slug.")
    asset_parser.add_argument("asset_type", choices=ASSET_TYPES)
    asset_parser.add_argument("--entity")
    asset_parser.add_argument("--shot", type=int)
    asset_parser.add_argument("--line", type=int)
    asset_parser.add_argument("--cue")
    asset_parser.add_argument("--label", default="rough_cut")
    asset_parser.add_argument("--version", type=int, default=1)
    asset_parser.add_argument("--ext")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "init":
        return _init(root, args)
    if args.command == "pilot":
        return _pilot(root, args)
    if args.command == "request":
        return _request(root, args)
    if args.command == "stages":
        return _stages(args)
    if args.command == "prompt":
        return _prompt(root, args)
    if args.command == "request-stage":
        return _request_stage(root, args)
    if args.command == "status":
        return _status(root, args)
    if args.command == "collect":
        return _collect(root, args)
    if args.command == "validate":
        return _validate(root, args)
    if args.command == "review":
        return _review(root, args)
    if args.command == "asset-name":
        return _asset_name(root, args)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _init(root: Path, args: argparse.Namespace) -> int:
    spec = ProjectSpec(
        slug=args.slug,
        title=args.title,
        aspect_ratio=args.aspect_ratio,
        runtime=args.runtime,
        source_type=args.source_type,
    )
    written = init_project(root, spec, force=args.force)
    path = project_dir(root, args.slug)
    print(f"Project ready: {path}")
    if written:
        print("Wrote:")
        for target in written:
            print(f"  {target}")
    else:
        print("No template files were overwritten.")
    return 0


def _pilot(root: Path, args: argparse.Namespace) -> int:
    path = init_pilot_project(root, slug=args.slug, force=args.force)
    print(f"Pilot project ready: {path}")
    print("Next command:")
    print(f"  mythoframe request-stage {args.slug} adaptation")
    return 0


def _request(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    prompt = _load_prompt(args.prompt, args.prompt_file)
    metadata = _request_metadata(args)
    return _submit_request(
        path=path,
        stage=args.stage,
        prompt=prompt,
        mode=args.mode,
        metadata=metadata,
        acceptance_checklist=[],
        wait=args.wait,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.timeout_seconds,
    )


def _submit_request(
    *,
    path: Path,
    stage: str,
    prompt: str,
    mode: str,
    metadata: dict[str, str],
    acceptance_checklist: list[str],
    wait: bool,
    poll_seconds: float,
    timeout_seconds: float,
) -> int:

    if mode == "api_command":
        request = create_request(
            path,
            stage,
            prompt,
            mode=mode,
            metadata=metadata,
            acceptance_checklist=acceptance_checklist,
        )
        output_path = path / "outputs" / stage / f"{request.request_id}.md"
        ApiCommandProvider().generate(request.request_path, output_path)
        generated = output_path.read_text(encoding="utf-8").strip()
        request.response_path.write_text(
            request.response_path.read_text(encoding="utf-8") + generated + "\n",
            encoding="utf-8",
            newline="\n",
        )
        collected_path = collect_response(path, request.request_id)
        print(f"API command output: {collected_path}")
        return 0

    request = create_request(
        path,
        stage,
        prompt,
        mode=mode,
        metadata=metadata,
        acceptance_checklist=acceptance_checklist,
    )
    print(f"Request:  {request.request_path}")
    print(f"Response: {request.response_path}")

    if wait:
        timeout = None if timeout_seconds <= 0 else timeout_seconds
        wait_for_response(
            request.response_path,
            poll_seconds=poll_seconds,
            timeout_seconds=timeout,
        )
        output_path = collect_response(path, request.request_id)
        print(f"Collected: {output_path}")

    return 0


def _stages(args: argparse.Namespace) -> int:
    for spec in list_stage_specs():
        if args.verbose:
            artifacts = ", ".join(spec.output_artifacts)
            print(f"{spec.name:14} {spec.title} -> {artifacts}")
        else:
            print(spec.name)
    return 0


def _prompt(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    prompt = render_stage_prompt(
        root,
        path,
        args.stage,
        source_file=Path(args.source_file) if args.source_file else None,
    )
    if args.out:
        output = Path(args.out)
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(prompt, encoding="utf-8", newline="\n")
        print(f"Wrote prompt: {output}")
    else:
        print(prompt, end="")
    return 0


def _request_stage(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    spec = get_stage_spec(args.stage)
    prompt = render_stage_prompt(
        root,
        path,
        args.stage,
        source_file=Path(args.source_file) if args.source_file else None,
    )
    metadata = _request_metadata(args)
    metadata["expected_artifacts"] = ", ".join(spec.output_artifacts)
    metadata["expected_format"] = spec.expected_format
    metadata["stage_title"] = spec.title
    metadata["paste_target"] = "matching .response.md below <!-- MODEL_OUTPUT_BELOW -->"
    metadata["review_required"] = "true"
    metadata["cost_policy"] = "manual_file/codex_web by default; api_command only when explicitly configured"
    return _submit_request(
        path=path,
        stage=args.stage,
        prompt=prompt,
        mode=args.mode,
        metadata=metadata,
        acceptance_checklist=list(spec.acceptance_checklist),
        wait=args.wait,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.timeout_seconds,
    )


def _status(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    records = list_pending(path)
    if not records:
        print("No pending requests.")
        return 0

    for record in records:
        state = "ready" if is_ready(record.response_path) else "waiting"
        print(f"{state:7} {record.request_id} {record.response_path}")
    return 0


def _collect(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    records = list_pending(path)
    if args.request_id:
        records = [record for record in records if record.request_id == args.request_id]

    collected = 0
    for record in records:
        if is_ready(record.response_path):
            output_path = collect_response(path, record.request_id)
            print(f"Collected: {output_path}")
            collected += 1

    if collected == 0:
        print("No ready responses to collect.")
    return 0


def _validate(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    problems = validate_project(path)
    if problems:
        print("Project validation failed:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"Project validation passed: {path}")
    return 0


def _review(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    problems = validate_project(path)
    print(f"Project: {path}")
    if problems:
        print("Validation: failed")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("Validation: passed")

    print("\nStages:")
    for status in stage_statuses(path):
        print(f"  {status.stage:14} {status.status:7} {status.detail}")

    pending = pending_request_summary(path)
    print("\nRequests:")
    if pending:
        for summary in pending:
            print(f"  {summary}")
    else:
        print("  none")

    next_status = next_stage(path)
    print("\nNext:")
    if next_status is None:
        print("  All current stages look ready for review.")
    else:
        print(f"  Work on `{next_status.stage}`: {next_status.detail}")
        print(f"  mythoframe request-stage {args.slug} {next_status.stage}")
    return 1 if problems else 0


def _asset_name(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    print(
        asset_path(
            path,
            args.asset_type,
            project_slug=args.slug,
            entity=args.entity,
            shot=args.shot,
            line=args.line,
            cue=args.cue,
            label=args.label,
            version=args.version,
            ext=args.ext,
        )
    )
    return 0


def _load_prompt(inline: str | None, prompt_file: str | None) -> str:
    if inline and prompt_file:
        raise SystemExit("Use either --prompt or --prompt-file, not both.")
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8")
    if inline:
        return inline
    return (
        "Generate the next MythoFrame artifact for this stage. Preserve "
        "character consistency, cinematic shot logic, and structured output."
    )


def _add_request_metadata_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-model", help="Preferred model website or model name.")
    parser.add_argument("--target-site", help="Preferred web app URL or platform name.")
    parser.add_argument("--operator-notes", help="Notes for the human or Codex operator.")


def _request_metadata(args: argparse.Namespace) -> dict[str, str]:
    return {
        "target_model": getattr(args, "target_model", None) or "",
        "target_site": getattr(args, "target_site", None) or "",
        "operator_notes": getattr(args, "operator_notes", None) or "",
    }
