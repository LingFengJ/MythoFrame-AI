"""Command line interface for MythoFrame."""

from __future__ import annotations

import argparse
from pathlib import Path

from mythoframe.artifacts import apply_stage_output
from mythoframe.assets import ASSET_TYPES, asset_path
from mythoframe.bundle import pack_project, unpack_project
from mythoframe.diagnostics import has_failures, run_doctor
from mythoframe.guide import command_guide, provider_guide
from mythoframe.manual_queue import (
    collect_response,
    create_request,
    is_ready,
    list_completed,
    list_pending,
    wait_for_response,
)
from mythoframe.media import (
    import_asset,
    list_asset_candidates,
    missing_media,
    set_asset_status,
)
from mythoframe.output_tools import inspect_stage_output, repair_stage_output
from mythoframe.prompts import get_stage_spec, list_stage_specs, render_stage_prompt
from mythoframe.project import ProjectSpec, init_project, project_dir, validate_project
from mythoframe.pilot import init_pilot_project
from mythoframe.providers import ApiCommandProvider
from mythoframe.renderer import render_rough_cut
from mythoframe.schemas import ARTIFACT_STATUSES, GENERATION_MODES, STAGE_NAMES
from mythoframe.subtitles import export_subtitles
from mythoframe.timeline import export_edit_manifest, write_draft_edit_plan
from mythoframe.workflow import (
    latest_collected_outputs,
    next_stage,
    pending_request_summary,
    stage_statuses,
)


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

    guide_parser = subparsers.add_parser("guide", help="Print the normal command guide.")
    guide_parser.add_argument("slug", nargs="?", default="pilot-scene")

    subparsers.add_parser("providers", help="Print the Seedance-first provider/account guide.")

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

    pack_parser = subparsers.add_parser("pack", help="Pack a project, including ignored local work.")
    pack_parser.add_argument("slug", help="Project slug.")
    pack_parser.add_argument("--out", help="Bundle path. Defaults to bundles/<slug>_<timestamp>.mythoframe.zip.")

    unpack_parser = subparsers.add_parser("unpack", help="Unpack a MythoFrame project bundle.")
    unpack_parser.add_argument("bundle", help="Path to .mythoframe.zip bundle.")
    unpack_parser.add_argument("--slug", help="Optional new project slug.")
    unpack_parser.add_argument("--force", action="store_true", help="Replace an existing project.")

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

    requests_parser = subparsers.add_parser("requests", help="Show request dashboard.")
    requests_parser.add_argument("slug", help="Project slug.")
    requests_parser.add_argument("--completed", action="store_true", help="Include completed requests.")

    collect_parser = subparsers.add_parser("collect", help="Collect ready response files.")
    collect_parser.add_argument("slug", help="Project slug.")
    collect_parser.add_argument("--request-id", help="Collect one request id only.")

    apply_parser = subparsers.add_parser(
        "apply-output",
        help="Apply collected output to canonical project artifacts.",
    )
    apply_parser.add_argument("slug", help="Project slug.")
    apply_parser.add_argument("stage", choices=STAGE_NAMES, help="Workflow stage.")
    apply_parser.add_argument("--output-file", help="Specific collected output file. Defaults to latest.")
    apply_parser.add_argument(
        "--keep-invalid",
        action="store_true",
        help="Keep applied files even if project validation fails.",
    )

    inspect_output_parser = subparsers.add_parser("inspect-output", help="Inspect collected model output.")
    inspect_output_parser.add_argument("slug", help="Project slug.")
    inspect_output_parser.add_argument("stage", choices=STAGE_NAMES, help="Workflow stage.")
    inspect_output_parser.add_argument("--output-file", help="Specific collected output file. Defaults to latest.")

    repair_output_parser = subparsers.add_parser("repair-output", help="Mechanically normalize collected output.")
    repair_output_parser.add_argument("slug", help="Project slug.")
    repair_output_parser.add_argument("stage", choices=STAGE_NAMES, help="Workflow stage.")
    repair_output_parser.add_argument("--output-file", help="Specific collected output file. Defaults to latest.")

    validate_parser = subparsers.add_parser("validate", help="Validate project structure.")
    validate_parser.add_argument("slug", help="Project slug.")

    doctor_parser = subparsers.add_parser("doctor", help="Run operational readiness checks.")
    doctor_parser.add_argument("slug", nargs="?", help="Optional project slug.")
    doctor_parser.add_argument("--openai-smoke", action="store_true", help="Run a tiny OpenAI API smoke test.")
    doctor_parser.add_argument("--openai-model", default="gpt-4.1-mini")
    doctor_parser.add_argument("--openai-max-output-tokens", type=int, default=16)

    review_parser = subparsers.add_parser("review", help="Summarize project workflow status.")
    review_parser.add_argument("slug", help="Project slug.")

    draft_edit_parser = subparsers.add_parser(
        "draft-edit",
        help="Build edit_plan.json from local shot, video, voice, and sound files.",
    )
    draft_edit_parser.add_argument("slug", help="Project slug.")

    export_parser = subparsers.add_parser("export-manifest", help="Export a text edit manifest.")
    export_parser.add_argument("slug", help="Project slug.")
    export_parser.add_argument("--out", help="Output path. Defaults to assets/exports/edit_manifest.txt.")

    subtitles_parser = subparsers.add_parser("subtitles", help="Export subtitles from edit or voice data.")
    subtitles_parser.add_argument("slug", help="Project slug.")
    subtitles_parser.add_argument("--format", choices=("srt", "vtt"), default="srt")
    subtitles_parser.add_argument("--out", help="Output path. Defaults to assets/exports/subtitles.<format>.")

    render_parser = subparsers.add_parser(
        "render-rough-cut",
        help="Render a local rough cut with ffmpeg when media files exist.",
    )
    render_parser.add_argument("slug", help="Project slug.")
    render_parser.add_argument("--out", help="Output video path. Defaults to assets/exports/rough_cut.mp4.")

    next_parser = subparsers.add_parser("next", help="Create a request for the next incomplete stage.")
    next_parser.add_argument("slug", help="Project slug.")
    next_parser.add_argument(
        "--mode",
        choices=GENERATION_MODES,
        default="manual_file",
        help="Generation mode. Defaults to manual_file.",
    )
    next_parser.add_argument("--source-file", help="Optional source brief path.")
    _add_request_metadata_args(next_parser)

    assets_parser = subparsers.add_parser("assets", help="List generated asset candidates.")
    assets_parser.add_argument("slug", help="Project slug.")
    assets_parser.add_argument("--status", choices=ARTIFACT_STATUSES)

    import_asset_parser = subparsers.add_parser("import-asset", help="Copy/register a generated asset.")
    import_asset_parser.add_argument("slug", help="Project slug.")
    import_asset_parser.add_argument("asset_type", choices=ASSET_TYPES)
    import_asset_parser.add_argument("source", help="Local source file to import.")
    import_asset_parser.add_argument("--candidate-id")
    import_asset_parser.add_argument("--provider", default="")
    import_asset_parser.add_argument("--request-id", default="")
    import_asset_parser.add_argument("--notes", default="")
    import_asset_parser.add_argument("--entity")
    import_asset_parser.add_argument("--shot", type=int)
    import_asset_parser.add_argument("--line", type=int)
    import_asset_parser.add_argument("--cue")
    import_asset_parser.add_argument("--label", default="rough_cut")
    import_asset_parser.add_argument("--version", type=int, default=1)
    import_asset_parser.add_argument("--ext")
    import_asset_parser.add_argument("--force", action="store_true")

    select_asset_parser = subparsers.add_parser("select-asset", help="Select/reject an asset candidate.")
    select_asset_parser.add_argument("slug", help="Project slug.")
    select_asset_parser.add_argument("candidate_id")
    select_asset_parser.add_argument("--status", choices=ARTIFACT_STATUSES, default="selected")
    select_asset_parser.add_argument("--notes", default="")

    missing_media_parser = subparsers.add_parser("missing-media", help="Report referenced media files that are missing.")
    missing_media_parser.add_argument("slug", help="Project slug.")

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

    if args.command == "guide":
        print(command_guide(args.slug))
        return 0
    if args.command == "providers":
        print(provider_guide())
        return 0
    if args.command == "init":
        return _init(root, args)
    if args.command == "pilot":
        return _pilot(root, args)
    if args.command == "pack":
        return _pack(root, args)
    if args.command == "unpack":
        return _unpack(root, args)
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
    if args.command == "requests":
        return _requests(root, args)
    if args.command == "collect":
        return _collect(root, args)
    if args.command == "apply-output":
        return _apply_output(root, args)
    if args.command == "inspect-output":
        return _inspect_output(root, args)
    if args.command == "repair-output":
        return _repair_output(root, args)
    if args.command == "validate":
        return _validate(root, args)
    if args.command == "doctor":
        return _doctor(root, args)
    if args.command == "review":
        return _review(root, args)
    if args.command == "draft-edit":
        return _draft_edit(root, args)
    if args.command == "export-manifest":
        return _export_manifest(root, args)
    if args.command == "subtitles":
        return _subtitles(root, args)
    if args.command == "render-rough-cut":
        return _render_rough_cut(root, args)
    if args.command == "next":
        return _next(root, args)
    if args.command == "assets":
        return _assets(root, args)
    if args.command == "import-asset":
        return _import_asset(root, args)
    if args.command == "select-asset":
        return _select_asset(root, args)
    if args.command == "missing-media":
        return _missing_media(root, args)
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


def _pack(root: Path, args: argparse.Namespace) -> int:
    output = Path(args.out) if args.out else None
    if output is not None and not output.is_absolute():
        output = root / output
    result = pack_project(root, args.slug, output_path=output)
    print(f"Packed {result.files} file(s): {result.path}")
    return 0


def _unpack(root: Path, args: argparse.Namespace) -> int:
    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = root / bundle
    result = unpack_project(root, bundle, slug=args.slug, force=args.force)
    print(f"Unpacked {result.files} file(s): {result.path}")
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


def _requests(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    pending = list_pending(path)
    completed = list_completed(path) if args.completed else []

    print("Pending Requests:")
    if not pending:
        print("  none")
    for record in pending:
        state = "ready" if is_ready(record.response_path) else "waiting"
        target = _request_target(record.target_site, record.target_model)
        print(f"  {state:7} {record.stage:14} {record.mode:12} {target} {record.request_id}")

    if args.completed:
        print("\nCompleted Requests:")
        if not completed:
            print("  none")
        for record in completed:
            target = _request_target(record.target_site, record.target_model)
            print(f"  done    {record.stage:14} {record.mode:12} {target} {record.request_id}")
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


def _apply_output(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    output_file = Path(args.output_file) if args.output_file else None
    if output_file is not None and not output_file.is_absolute():
        output_file = root / output_file
    result = apply_stage_output(
        path,
        args.stage,
        output_path=output_file,
        keep_invalid=args.keep_invalid,
    )
    print(f"Applied: {result.output_path}")
    for written in result.written_files:
        print(f"  {written}")
    if result.backup_dir is not None:
        print(f"Backup: {result.backup_dir}")
    return 0


def _inspect_output(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    output_file = Path(args.output_file) if args.output_file else None
    if output_file is not None and not output_file.is_absolute():
        output_file = root / output_file
    inspection = inspect_stage_output(path, args.stage, output_path=output_file)
    print(f"Output: {inspection.output_path}")
    print(f"Stage: {inspection.stage}")
    print(f"Parse: {'ok' if inspection.parse_ok else 'failed'}")
    print(f"Targets: {', '.join(inspection.targets)}")
    for message in inspection.messages:
        print(f"- {message}")
    return 0 if inspection.parse_ok else 1


def _repair_output(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    output_file = Path(args.output_file) if args.output_file else None
    if output_file is not None and not output_file.is_absolute():
        output_file = root / output_file
    repaired = repair_stage_output(path, args.stage, output_path=output_file)
    print(f"Wrote repaired output: {repaired}")
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


def _doctor(root: Path, args: argparse.Namespace) -> int:
    project_path = project_dir(root, args.slug) if args.slug else None
    checks = run_doctor(
        root,
        project_path,
        openai_smoke=args.openai_smoke,
        openai_model=args.openai_model,
        openai_max_output_tokens=args.openai_max_output_tokens,
    )
    for check in checks:
        print(f"{check.status:4} {check.name:18} {check.detail}")
    return 1 if has_failures(checks) else 0


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

    outputs = latest_collected_outputs(path)
    print("\nCollected Outputs:")
    if outputs:
        for stage, output in outputs.items():
            print(f"  {stage:14} {output}")
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


def _draft_edit(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    output = write_draft_edit_plan(path)
    problems = validate_project(path)
    print(f"Wrote draft edit plan: {output}")
    if problems:
        print("Project validation failed:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    return 0


def _export_manifest(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    output_path = Path(args.out) if args.out else None
    if output_path is not None and not output_path.is_absolute():
        output_path = root / output_path
    output = export_edit_manifest(path, output_path=output_path)
    print(f"Wrote edit manifest: {output}")
    return 0


def _subtitles(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    output_path = Path(args.out) if args.out else None
    if output_path is not None and not output_path.is_absolute():
        output_path = root / output_path
    output = export_subtitles(path, fmt=args.format, output_path=output_path)
    print(f"Wrote subtitles: {output}")
    return 0


def _render_rough_cut(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    output_path = Path(args.out) if args.out else None
    if output_path is not None and not output_path.is_absolute():
        output_path = root / output_path
    output = render_rough_cut(path, output_path=output_path)
    print(f"Wrote rough cut: {output}")
    return 0


def _next(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    status = next_stage(path)
    if status is None:
        print("All current stages look ready for review.")
        return 0
    spec = get_stage_spec(status.stage)
    prompt = render_stage_prompt(
        root,
        path,
        status.stage,
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
        stage=status.stage,
        prompt=prompt,
        mode=args.mode,
        metadata=metadata,
        acceptance_checklist=list(spec.acceptance_checklist),
        wait=False,
        poll_seconds=10.0,
        timeout_seconds=0.0,
    )


def _assets(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    candidates = list_asset_candidates(path, status=args.status)
    if not candidates:
        print("No asset candidates.")
        return 0
    for candidate in candidates:
        print(
            f"{candidate.get('status', ''):12} "
            f"{candidate.get('asset_type', ''):12} "
            f"{candidate.get('candidate_id', '')} "
            f"{candidate.get('path', '')}"
        )
    return 0


def _import_asset(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    source = Path(args.source)
    if not source.is_absolute():
        source = root / source
    result = import_asset(
        path,
        source,
        args.asset_type,
        candidate_id=args.candidate_id,
        provider=args.provider,
        request_id=args.request_id,
        notes=args.notes,
        entity=args.entity,
        shot=args.shot,
        line=args.line,
        cue=args.cue,
        label=args.label,
        version=args.version,
        ext=args.ext,
        force=args.force,
    )
    print(f"Imported: {result.destination}")
    print(f"Candidate: {result.candidate_id}")
    print(f"Manifest: {result.manifest_path}")
    return 0


def _select_asset(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    result = set_asset_status(
        path,
        args.candidate_id,
        status=args.status,
        notes=args.notes,
    )
    print(f"Candidate: {result.candidate_id}")
    print(f"Status: {result.status}")
    print("Updated:")
    for updated in result.updated_files:
        print(f"  {updated}")
    return 0


def _missing_media(root: Path, args: argparse.Namespace) -> int:
    path = project_dir(root, args.slug)
    missing = missing_media(path)
    if not missing:
        print("No missing referenced media.")
        return 0
    print("Missing referenced media:")
    for item in missing:
        print(f"  {item.source} {item.field}: {item.path}")
    return 1


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


def _request_target(site: str, model: str) -> str:
    parts = [part for part in (site, model) if part]
    if not parts:
        return "-"
    return "/".join(parts)
