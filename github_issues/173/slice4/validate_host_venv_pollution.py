#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_host_venv_pollution.py HOST_VENV_POLLUTION_JSON", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "before_freeze",
        "after_freeze",
        "added_packages",
        "removed_packages",
        "host_venv_pollution_detected",
    }
    missing = sorted(required - set(data))
    if missing:
        print(f"missing keys: {missing}", file=sys.stderr)
        return 1
    if data["host_venv_pollution_detected"] is not False:
        print("host_venv_pollution_detected is not false", file=sys.stderr)
        return 1
    if data["added_packages"] != []:
        print(f"added_packages is not empty: {data['added_packages']}", file=sys.stderr)
        return 1
    if data["removed_packages"] != []:
        print(f"removed_packages is not empty: {data['removed_packages']}", file=sys.stderr)
        return 1
    if not isinstance(data["after_freeze"], list) or not data["after_freeze"]:
        print("after_freeze must be a non-empty list", file=sys.stderr)
        return 1
    print("host venv pollution validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
