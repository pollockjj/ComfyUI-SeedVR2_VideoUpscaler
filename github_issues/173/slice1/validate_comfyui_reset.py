#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED_SHA = "61dbc1aeb7b69a0ee41521d56f36cedd573291f4"


def main() -> int:
    print("$ python " + " ".join(sys.argv))
    if len(sys.argv) != 2:
        print("ERROR: expected one JSON artifact path")
        print("EXIT_CODE: 2")
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    expected = {
        "upstream_pyisolate_support_sha": EXPECTED_SHA,
        "origin_pyisolate_support_sha_after_reset": EXPECTED_SHA,
        "local_head_after_reset": EXPECTED_SHA,
        "binary_equal": True,
    }
    failures = [
        f"{key}: expected {value!r}, got {data.get(key)!r}"
        for key, value in expected.items()
        if data.get(key) != value
    ]
    if failures:
        print("ERROR: ComfyUI reset validation failed")
        for failure in failures:
            print(failure)
        print("EXIT_CODE: 1")
        return 1
    print("comfyui_force_reset: valid")
    print("EXIT_CODE: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
