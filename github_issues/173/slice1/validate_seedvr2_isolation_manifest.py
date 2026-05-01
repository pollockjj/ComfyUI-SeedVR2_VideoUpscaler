#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path


def main() -> int:
    print("$ python " + " ".join(sys.argv))
    if len(sys.argv) != 3:
        print("ERROR: expected pyproject path and canonical runtime JSON path")
        print("EXIT_CODE: 2")
        return 2
    pyproject = tomllib.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    canonical = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    isolation = pyproject.get("tool", {}).get("comfy", {}).get("isolation", {})
    expected = {
        "can_isolate": True,
        "share_torch": True,
        "package_manager": "uv",
        "execution_model": "host-coupled",
        "share_torch_no_deps": canonical["share_torch_no_deps"],
    }
    failures = [
        f"{key}: expected {value!r}, got {isolation.get(key)!r}"
        for key, value in expected.items()
        if isolation.get(key) != value
    ]
    if failures:
        print("ERROR: isolation manifest validation failed")
        for failure in failures:
            print(failure)
        print("EXIT_CODE: 1")
        return 1
    print("seedvr2_isolation_manifest: valid")
    print("EXIT_CODE: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
