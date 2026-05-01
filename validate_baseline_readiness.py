#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED = {
    "baseline_collection_ready": True,
    "torch_share_passed": True,
    "isolated_smoke_passed": True,
    "output_video_validated": True,
    "node_registration_present": True,
    "submitted_branch_provenance_verified": True,
    "sealed_worker_fallback_used": False,
}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_baseline_readiness.py BASELINE_READINESS_JSON", file=sys.stderr)
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for key, expected in EXPECTED.items():
        actual = data.get(key)
        if actual is not expected:
            print(f"{key} expected {expected!r}, got {actual!r}", file=sys.stderr)
            return 1
    print("baseline readiness validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
