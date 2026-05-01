import json
import sys
from pathlib import Path


def main(path: str) -> int:
    data = json.loads(Path(path).read_text())
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
    elif not Path(output_video_path).exists():
        failures.append(f"output_video_path: path does not exist: {output_video_path}")
    if failures:
        print("FAIL")
        for failure in failures:
            print(failure)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
