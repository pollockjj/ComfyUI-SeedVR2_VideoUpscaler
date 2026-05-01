#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def freeze_lines(text: str) -> list[str]:
    ignored_prefixes = ("$", "EXIT_CODE:", "STDERR:")
    retained_requirement_markers = ("==", " @ ")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(prefix) for prefix in ignored_prefixes):
            continue
        if line.startswith("#"):
            continue
        if line.startswith("-e ") or line.startswith("--editable "):
            lines.append(line)
            continue
        if "://" in line:
            lines.append(line)
            continue
        if not any(marker in line for marker in retained_requirement_markers):
            lines.append(line)
            continue
        lines.append(line)
    return sorted(lines, key=str.lower)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    before = freeze_lines(args.before.read_text(encoding="utf-8"))
    result = subprocess.run(
        [args.python, "-m", "pip", "freeze"],
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
        "exit_code": result.returncode,
    }
    if result.stderr.strip():
        payload["stderr"] = result.stderr.strip()
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
