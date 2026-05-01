from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED = {
    "input_video_sha256": "21581bc8454e234e3d3f833172bb358215f47d33cfcf5fc12f3dd0dff3319d1d",
    "width": 640,
    "height": 360,
    "r_frame_rate": "25/1",
    "nb_frames": 45,
    "pos_emb.pt": "fa07a14844314772266b66c3b95deb0027696d8fe7065721263db5176f45d799",
    "neg_emb.pt": "6a43e5800ef2354f1c156d27535834da055cbec8248298b8923492bba2076581",
    "seedvr2_ema_3b_fp16.safetensors": "2fd0e03a3dad24e07086750360727ca437de4ecd456f769856e960ae93e2b304",
    "ema_vae_fp16.safetensors": "20678548f420d98d26f11442d3528f8b8c94e57ee046ef93dbb7633da8612ca1",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: validate_asset_manifest.py asset_manifest.json")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    video = data.get("input_video", {})
    if video.get("sha256") != EXPECTED["input_video_sha256"]:
        fail("input video SHA mismatch")
    if not video.get("source_path"):
        fail("input video source path missing")
    if not video.get("stage_path"):
        fail("input video staged path missing")
    if video.get("width") != EXPECTED["width"]:
        fail("input video width mismatch")
    if video.get("height") != EXPECTED["height"]:
        fail("input video height mismatch")
    if video.get("r_frame_rate") != EXPECTED["r_frame_rate"]:
        fail("input video frame rate mismatch")
    if int(video.get("nb_frames")) != EXPECTED["nb_frames"]:
        fail("input video frame count mismatch")

    bundled = data.get("bundled_assets", {})
    for asset in ("pos_emb.pt", "neg_emb.pt"):
        if bundled.get(asset, {}).get("sha256") != EXPECTED[asset]:
            fail(f"{asset} SHA mismatch")

    model_hashes = data.get("model_hashes", {})
    for model in ("seedvr2_ema_3b_fp16.safetensors", "ema_vae_fp16.safetensors"):
        if model_hashes.get(model, {}).get("registry_sha256") != EXPECTED[model]:
            fail(f"{model} registry SHA mismatch")
    print("PASS: asset manifest validation matched Slice 2 AC-4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
