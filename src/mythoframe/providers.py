"""Generation provider hooks.

The default provider is intentionally file-based. API automation is available
only through explicit configuration so expensive calls cannot happen by accident.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ApiCommandResult:
    output_path: Path


class ApiCommandProvider:
    """Run a user-supplied API wrapper command.

    The wrapper receives two arguments: prompt file path and output file path.
    This keeps provider-specific SDKs and paid API calls outside the default
    project path while still making automation possible.
    """

    env_var = "MYTHOFRAME_API_COMMAND"

    def generate(self, prompt_path: Path, output_path: Path) -> ApiCommandResult:
        command = os.environ.get(self.env_var, "").strip()
        if not command:
            raise RuntimeError(
                "API generation is opt-in. Set MYTHOFRAME_API_COMMAND to a "
                "local wrapper command before using api_command mode."
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([command, str(prompt_path), str(output_path)], check=True)
        if not output_path.exists() or not output_path.read_text(encoding="utf-8").strip():
            raise RuntimeError(f"API wrapper did not write output: {output_path}")
        return ApiCommandResult(output_path=output_path)

