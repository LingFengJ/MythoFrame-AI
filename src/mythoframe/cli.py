"""Command line interface for MythoFrame."""

from __future__ import annotations

import argparse
from pathlib import Path

from mythoframe.manual_queue import (
    collect_response,
    create_request,
    is_ready,
    list_pending,
    wait_for_response,
)
from mythoframe.project import ProjectSpec, init_project, project_dir, validate_project
from mythoframe.providers import ApiCommandProvider
from mythoframe.schemas import GENERATION_MODES


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

    status_parser = subparsers.add_parser("status", help="Show pending generation requests.")
    status_parser.add_argument("slug", help="Project slug.")

    collect_parser = subparsers.add_parser("collect", help="Collect ready response files.")
    collect_parser.add_argument("slug", help="Project slug.")
    collect_parser.add_argument("--request-id", help="Collect one request id only.")

    validate_parser = subparsers.add_parser("validate", help="Validate project structure.")
    validate_parser.add_argument("slug", help="Project slug.")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command == "init":
        return _init(root, args)
    if args.command == "request":
        return _request(root, args)
    if args.command == "status":
        return _status(root, args)
    if args.command == "collect":
        return _collect(root, args)
    if args.command == "validate":
        return _validate(root, args)

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


def _request(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    prompt = _load_prompt(args.prompt, args.prompt_file)

    if args.mode == "api_command":
        request = create_request(path, args.stage, prompt, mode=args.mode)
        output_path = path / "outputs" / args.stage / f"{request.request_id}.md"
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

    request = create_request(path, args.stage, prompt, mode=args.mode)
    print(f"Request:  {request.request_path}")
    print(f"Response: {request.response_path}")

    if args.wait:
        timeout = None if args.timeout_seconds <= 0 else args.timeout_seconds
        wait_for_response(
            request.response_path,
            poll_seconds=args.poll_seconds,
            timeout_seconds=timeout,
        )
        output_path = collect_response(path, request.request_id)
        print(f"Collected: {output_path}")

    return 0


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
