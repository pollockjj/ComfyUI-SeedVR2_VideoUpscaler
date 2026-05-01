from __future__ import annotations

import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: assert_workflow_validation.py workflow_validation.json")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    expected_create = {
        "images": "SeedVR2VideoUpscaler",
        "audio": "GetVideoComponents.audio",
        "fps": "GetVideoComponents.fps",
    }
    if data.get("seedvr2_image_source") != ["GetVideoComponents", "images"]:
        fail("SeedVR2 image source mismatch")
    if data.get("join_image_with_alpha_present") is not False:
        fail("JoinImageWithAlpha present")
    if data.get("note_nodes_present") is not False:
        fail("Note nodes present")
    if data.get("create_video_inputs") != expected_create:
        fail("CreateVideo input producer map mismatch")
    prefix = data.get("save_video_prefix", "")
    if not (prefix.startswith("video/ComfyUI") or prefix.startswith("video/issue_173")):
        fail("SaveVideo prefix is outside the accepted roots")
    print("PASS: workflow contract validation matched Slice 2 AC-2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
