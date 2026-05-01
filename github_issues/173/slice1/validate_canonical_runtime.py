#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED_NO_DEPS = [
    "einops",
    "antlr4-python3-runtime",
    "omegaconf",
    "opencv-python",
    "numpy",
    "av",
    "diffusers",
    "rotary-embedding-torch",
    "transformers",
    "tokenizers",
    "huggingface-hub",
    "safetensors",
    "mediapy",
    "ipython",
    "matplotlib",
    "beartype",
]


def main() -> int:
    print("$ python " + " ".join(sys.argv))
    if len(sys.argv) != 2:
        print("ERROR: expected one JSON artifact path")
        print("EXIT_CODE: 2")
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    expected = {
        "canonical_repo": "pollockjj/ComfyUI-SeedVR2-Canonical",
        "canonical_branch": "issue_155",
        "canonical_commit": "0035a28ffefc615e37b1da40c3fe41ba9d1f8cba",
        "torch": "2.4.0+cu121",
        "torchvision": "0.19.0+cu121",
        "package_manager": "uv",
        "execution_model": "host-coupled",
        "share_torch": True,
        "share_torch_no_deps": EXPECTED_NO_DEPS,
    }
    required_keys = set(expected) | {"python_requirement", "cuda_tuple", "runtime_fixes"}
    failures = [f"{key}: missing" for key in sorted(required_keys) if key not in data]
    failures.extend(
        f"{key}: expected {value!r}, got {data.get(key)!r}"
        for key, value in expected.items()
        if data.get(key) != value
    )
    if failures:
        print("ERROR: canonical runtime validation failed")
        for failure in failures:
            print(failure)
        print("EXIT_CODE: 1")
        return 1
    print("canonical_runtime_requirements: valid")
    print("EXIT_CODE: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
