import json
import sys
from pathlib import Path


def main(smoke_path: str, stop_packet_path: str) -> int:
    smoke = json.loads(Path(smoke_path).read_text())
    if smoke.get("torch_share_passed") is True:
        if smoke.get("sealed_worker_used") is not False:
            print("FAIL")
            print("sealed_worker_used must be false when torch_share_passed is true")
            return 1
        print("PASS")
        return 0

    stop_packet = Path(stop_packet_path)
    if not stop_packet.exists():
        print("FAIL")
        print(f"stop packet missing: {stop_packet}")
        return 1
    content = stop_packet.read_text()
    required_lines = [
        "torch_share_passed: false",
        "sealed_worker_fallback: blocked",
        "next_required_decision: re-evaluate torch_share failure",
    ]
    missing = [line for line in required_lines if line not in content.splitlines()]
    if missing:
        print("FAIL")
        for line in missing:
            print(f"missing line: {line}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
