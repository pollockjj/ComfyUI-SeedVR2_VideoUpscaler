#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_LINES = [
    "baseline_collection_ready: true",
    "torch_share_passed: true",
    "isolated_smoke_passed: true",
    "output_video_validated: true",
    "host_venv_pollution_detected: false",
    "sealed_worker_fallback_used: false",
    "next_action: begin SeedVR2 baseline collection in a separate issue",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_baseline_readiness_md.py BASELINE_READINESS_MD", file=sys.stderr)
        return 2
    lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    missing = [line for line in REQUIRED_LINES if line not in lines]
    if missing:
        print(f"missing required lines: {missing}", file=sys.stderr)
        return 1
    print("baseline readiness markdown validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
