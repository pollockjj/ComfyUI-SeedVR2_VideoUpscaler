#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def resolve_python(requested: str) -> str:
    if requested != "python":
        return requested
    workspace = Path(__file__).resolve().parents[3]
    host_python = workspace.parent / "ComfyUI" / ".venv" / "bin" / "python"
    if host_python.exists():
        return str(host_python)
    return requested


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    command_line = "$ python github_issues/173/slice1/capture_host_venv_freeze.py --python python --out github_issues/173/slice1/host_venv_freeze_before.txt"
    result = subprocess.run(
        [resolve_python(args.python), "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = sorted((line.strip() for line in result.stdout.splitlines() if line.strip()), key=str.lower)
    body = [command_line, f"EXIT_CODE: {result.returncode}", ""]
    if lines:
        body.extend(lines)
    if result.stderr.strip():
        body.extend(["", "STDERR:", result.stderr.strip()])
    args.out.write_text("\n".join(body) + "\n", encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
