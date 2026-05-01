import json
import sys
from pathlib import Path


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
        elif not Path(value).exists():
            failures.append(f"{key}: path does not exist: {value}")
    if failures:
        print("FAIL")
        for failure in failures:
            print(failure)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
