from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED = {
    "dit": {
        "model": "seedvr2_ema_3b_fp16.safetensors",
        "device": "cuda:0",
        "blocks_to_swap": 32,
        "swap_io_components": False,
        "offload_device": "cpu",
        "cache_model": False,
        "attention_mode": "sdpa",
    },
    "vae": {
        "model": "ema_vae_fp16.safetensors",
        "device": "cuda:0",
        "encode_tiled": True,
        "encode_tile_size": 1024,
        "encode_tile_overlap": 128,
        "decode_tiled": True,
        "decode_tile_size": 768,
        "decode_tile_overlap": 128,
        "tile_debug": "false",
        "offload_device": "cpu",
        "cache_model": False,
    },
    "upscaler": {
        "seed": 42,
        "resolution": 1080,
        "max_resolution": 0,
        "batch_size": 33,
        "uniform_batch_size": True,
        "color_correction": "lab",
        "temporal_overlap": 3,
        "prepend_frames": 0,
        "input_noise_scale": 0,
        "latent_noise_scale": 0,
        "offload_device": "cpu",
        "enable_debug": False,
    },
    "compile": {
        "backend": "inductor",
        "mode": "default",
        "fullgraph": False,
        "dynamic": False,
        "dynamo_cache_size_limit": 64,
        "dynamo_recompile_limit": 128,
    },
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: assert_hd_settings.py workflow_validation.json")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    settings = data.get("settings_preserved", {})
    for section, expected in EXPECTED.items():
        actual = settings.get(section, {})
        for key, value in expected.items():
            if actual.get(key) != value:
                fail(f"{section}.{key} expected {value!r}, got {actual.get(key)!r}")
    if settings.get("hidden_fixed_absent") is not True:
        fail("hidden UI value fixed is not recorded absent")
    print("PASS: HD settings validation matched Slice 2 AC-3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
