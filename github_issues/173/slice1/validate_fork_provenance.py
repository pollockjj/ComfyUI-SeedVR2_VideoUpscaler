#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED = {
    "upstream_url": "https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler",
    "fork_url": "git@github.com:pollockjj/ComfyUI-SeedVR2_VideoUpscaler.git",
    "target_version": "2.5.24",
    "starting_commit_sha": "4490bd1f482e026674543386bb2a4d176da245b9",
    "conversion_branch": "issue_173",
    "origin_main_sha": "4490bd1f482e026674543386bb2a4d176da245b9",
    "origin_pyisolate_support_exists": False,
}


def main() -> int:
    print("$ python " + " ".join(sys.argv))
    if len(sys.argv) != 2:
        print("ERROR: expected one JSON artifact path")
        print("EXIT_CODE: 2")
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    failures = [
        f"{key}: expected {expected!r}, got {data.get(key)!r}"
        for key, expected in EXPECTED.items()
        if data.get(key) != expected
    ]
    extra_missing = [key for key in EXPECTED if key not in data]
    failures.extend(f"{key}: missing" for key in extra_missing)
    if failures:
        print("ERROR: fork provenance validation failed")
        for failure in failures:
            print(failure)
        print("EXIT_CODE: 1")
        return 1
    print("fork_provenance: valid")
    print("EXIT_CODE: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
