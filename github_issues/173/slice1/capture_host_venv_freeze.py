#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def resolve_python(requested: str) -> str:
    if requested != "python":
        return requested
    workspace = Path(__file__).resolve().parents[3]
    candidates = [workspace.parent / "ComfyUI" / ".venv" / "bin" / "python"]
    for parent in Path(__file__).resolve().parents:
        if parent.name == "ComfyUI":
            candidates.append(parent / ".venv" / "bin" / "python")
            break
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    print(
        "FAIL: --python python did not resolve to a slot-local host venv interpreter: "
        + ", ".join(str(candidate) for candidate in candidates),
        file=sys.stderr,
    )
    raise SystemExit(1)


def shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    resolved_python = resolve_python(args.python)
    command_line = "$ " + shell_command([sys.executable, *sys.argv])
    pip_freeze_command = shell_command([resolved_python, "-m", "pip", "freeze"])
    result = subprocess.run(
        [resolved_python, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = sorted((line.strip() for line in result.stdout.splitlines() if line.strip()), key=str.lower)
    body = [
        command_line,
        f"# RESOLVED_PYTHON: {resolved_python}",
        f"# PIP_FREEZE_COMMAND: {pip_freeze_command}",
        f"EXIT_CODE: {result.returncode}",
        "",
    ]
    if lines:
        body.extend(lines)
    if result.stderr.strip():
        body.extend(["", "STDERR:", result.stderr.strip()])
    args.out.write_text("\n".join(body) + "\n", encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
