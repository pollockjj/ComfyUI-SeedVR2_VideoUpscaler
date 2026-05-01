import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMFY_ROOT = REPO_ROOT.parents[1]


def resolve_evidence_path(value: str) -> Path:
    if value.startswith("ComfyUI:"):
        return COMFY_ROOT / value.removeprefix("ComfyUI:")
    if value.startswith("custom_node:"):
        return REPO_ROOT / value.removeprefix("custom_node:")
    return Path(value)


def main(path: str) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    failures = []
    expected = {
        "width": 1920,
        "height": 1080,
        "nb_frames": 45,
        "r_frame_rate": "25/1",
    }
    for key, value in expected.items():
        if data.get(key) != value:
            failures.append(f"{key}: expected {value!r}, got {data.get(key)!r}")
    if data.get("size_bytes", 0) <= 0:
        failures.append(f"size_bytes: expected > 0, got {data.get('size_bytes')!r}")
    output_video_path = data.get("output_video_path")
    if not output_video_path:
        failures.append("output_video_path: missing")
    elif not resolve_evidence_path(output_video_path).exists():
        failures.append(f"output_video_path: path does not exist: {output_video_path}")
    if failures:
        print("FAIL")
        for failure in failures:
            print(failure)
        return 1
    print("PASS")
    return 0


def cli(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: validate_output_video.py <output_video_ffprobe.json>", file=sys.stderr)
        return 2
    return main(argv[0])


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
