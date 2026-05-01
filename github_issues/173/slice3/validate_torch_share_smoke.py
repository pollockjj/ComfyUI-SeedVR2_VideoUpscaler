import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMFY_ROOT = REPO_ROOT.parents[1]
MYDEVELOPMENT_ROOT = COMFY_ROOT.parent / "mydevelopment"


def resolve_evidence_path(value: str) -> Path:
    prefixes = {
        "ComfyUI:": COMFY_ROOT,
        "mydevelopment:": MYDEVELOPMENT_ROOT,
        "custom_node:": REPO_ROOT,
    }
    for prefix, root in prefixes.items():
        if value.startswith(prefix):
            return root / value.removeprefix(prefix)
    return Path(value)


def main(path: str) -> int:
    data = json.loads(Path(path).read_text())
    expected = {
        "manifest_share_torch": True,
        "execution_model": "host-coupled",
        "exit_code": 0,
        "torch_share_passed": True,
        "sealed_worker_used": False,
    }
    failures = []
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"{key}: expected {value!r}, got {data.get(key)!r}")
    for key in ("harness_run_artifact_dir", "output_video_path"):
        value = data.get(key)
        if not value:
            failures.append(f"{key}: missing")
        elif not resolve_evidence_path(value).exists():
            failures.append(f"{key}: path does not exist: {value}")
    if failures:
        print("FAIL")
        for failure in failures:
            print(failure)
        return 1
    print("PASS")
    return 0


def cli(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: validate_torch_share_smoke.py <torch_share_smoke.json>", file=sys.stderr)
        return 2
    return main(argv[0])


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
