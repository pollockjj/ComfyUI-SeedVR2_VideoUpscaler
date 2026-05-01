#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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


def freeze_lines(text: str) -> list[str]:
    ignored_prefixes = ("$", "EXIT_CODE:", "STDERR:")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(prefix) for prefix in ignored_prefixes):
            continue
        if line.startswith("#"):
            continue
        lines.append(line)
    return sorted(lines, key=str.lower)


def shell_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    before = freeze_lines(args.before.read_text(encoding="utf-8"))
    resolved_python = resolve_python(args.python)
    result = subprocess.run(
        [resolved_python, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    )
    after = freeze_lines(result.stdout)
    added = sorted(set(after) - set(before), key=str.lower)
    removed = sorted(set(before) - set(after), key=str.lower)
    payload = {
        "before_freeze": str(args.before),
        "after_freeze": after,
        "added_packages": added,
        "removed_packages": removed,
        "host_venv_pollution_detected": bool(added or removed),
        "command": shell_command([sys.executable, *sys.argv]),
        "resolved_python": resolved_python,
        "pip_freeze_command": shell_command([resolved_python, "-m", "pip", "freeze"]),
        "exit_code": result.returncode,
    }
    if result.stderr.strip():
        payload["stderr"] = result.stderr.strip()
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
