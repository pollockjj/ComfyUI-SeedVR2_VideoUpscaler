from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_CLASS_TYPES = [
    "LoadVideo",
    "GetVideoComponents",
    "SeedVR2LoadDiTModel",
    "SeedVR2LoadVAEModel",
    "SeedVR2TorchCompileSettings",
    "SeedVR2VideoUpscaler",
    "CreateVideo",
    "SaveVideo",
]
FORBIDDEN_CLASS_TYPES = ["Note", "JoinImageWithAlpha"]

EXPECTED_COMPILE = {
    "backend": "inductor",
    "mode": "default",
    "fullgraph": False,
    "dynamic": False,
    "dynamo_cache_size_limit": 64,
    "dynamo_recompile_limit": 128,
}
EXPECTED_DIT = {
    "model": "seedvr2_ema_3b_fp16.safetensors",
    "device": "cuda:0",
    "blocks_to_swap": 32,
    "swap_io_components": False,
    "offload_device": "cpu",
    "cache_model": False,
    "attention_mode": "sdpa",
}
EXPECTED_VAE = {
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
}
EXPECTED_UPSCALER = {
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
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def node_by_class(api: dict[str, Any], class_type: str) -> tuple[str, dict[str, Any]]:
    matches = [(node_id, node) for node_id, node in api.items() if node.get("class_type") == class_type]
    if len(matches) != 1:
        fail(f"expected exactly one {class_type}, found {len(matches)}")
    return matches[0]


def source_node_by_type(source: dict[str, Any], node_type: str) -> dict[str, Any]:
    nodes = source.get("nodes")
    if not isinstance(nodes, list):
        fail("source workflow does not contain a nodes list")
    matches = [node for node in nodes if node.get("type") == node_type]
    if len(matches) != 1:
        fail(f"source expected exactly one {node_type}, found {len(matches)}")
    return matches[0]


def assert_subset(actual: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    for key, value in expected.items():
        if actual.get(key) != value:
            fail(f"{label}.{key} expected {value!r}, got {actual.get(key)!r}")


def validated_api_class_types(api: Any) -> list[str]:
    if not isinstance(api, dict):
        fail(f"API prompt root must be an object, got {type(api).__name__}")

    class_types: list[str] = []
    for node_id, node in api.items():
        if not isinstance(node, dict):
            fail(f"API node {node_id!r} must be an object, got {type(node).__name__}")
        class_type = node.get("class_type")
        if not isinstance(class_type, str):
            fail(f"API node {node_id!r} missing string class_type")
        class_types.append(class_type)
    return sorted(class_types)


def contains_literal_value(node: Any, expected: Any) -> bool:
    if isinstance(node, dict):
        return any(contains_literal_value(value, expected) for value in node.values())
    if isinstance(node, list):
        return any(contains_literal_value(value, expected) for value in node)
    return node == expected


def assert_source_widgets(source: dict[str, Any]) -> None:
    expected_widgets = {
        "SeedVR2TorchCompileSettings": ["inductor", "default", False, False, 64, 128],
        "SeedVR2LoadDiTModel": [
            EXPECTED_DIT["model"],
            EXPECTED_DIT["device"],
            EXPECTED_DIT["blocks_to_swap"],
            EXPECTED_DIT["swap_io_components"],
            EXPECTED_DIT["offload_device"],
            EXPECTED_DIT["cache_model"],
            EXPECTED_DIT["attention_mode"],
        ],
        "SeedVR2LoadVAEModel": [
            EXPECTED_VAE["model"],
            EXPECTED_VAE["device"],
            EXPECTED_VAE["encode_tiled"],
            EXPECTED_VAE["encode_tile_size"],
            EXPECTED_VAE["encode_tile_overlap"],
            EXPECTED_VAE["decode_tiled"],
            EXPECTED_VAE["decode_tile_size"],
            EXPECTED_VAE["decode_tile_overlap"],
            EXPECTED_VAE["tile_debug"],
            EXPECTED_VAE["offload_device"],
            EXPECTED_VAE["cache_model"],
        ],
        "SeedVR2VideoUpscaler": [
            EXPECTED_UPSCALER["seed"],
            "fixed",
            EXPECTED_UPSCALER["resolution"],
            EXPECTED_UPSCALER["max_resolution"],
            EXPECTED_UPSCALER["batch_size"],
            EXPECTED_UPSCALER["uniform_batch_size"],
            EXPECTED_UPSCALER["color_correction"],
            EXPECTED_UPSCALER["temporal_overlap"],
            EXPECTED_UPSCALER["prepend_frames"],
            EXPECTED_UPSCALER["input_noise_scale"],
            EXPECTED_UPSCALER["latent_noise_scale"],
            EXPECTED_UPSCALER["offload_device"],
            EXPECTED_UPSCALER["enable_debug"],
        ],
    }
    for node_type, expected in expected_widgets.items():
        actual = source_node_by_type(source, node_type).get("widgets_values")
        if actual != expected:
            fail(f"source {node_type} widgets expected {expected!r}, got {actual!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--api", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    source = load_json(args.source)
    api = load_json(args.api)
    assert_source_widgets(source)

    class_types = validated_api_class_types(api)
    forbidden_present = sorted(set(class_types) & set(FORBIDDEN_CLASS_TYPES))
    if forbidden_present:
        fail(f"forbidden class_type entries present: {forbidden_present}")
    if class_types != sorted(REQUIRED_CLASS_TYPES):
        fail(f"class_type set mismatch: {class_types}")

    upscaler_id, upscaler = node_by_class(api, "SeedVR2VideoUpscaler")
    load_video_id, _ = node_by_class(api, "LoadVideo")
    components_id, components = node_by_class(api, "GetVideoComponents")
    create_id, create_video = node_by_class(api, "CreateVideo")
    save_id, save_video = node_by_class(api, "SaveVideo")
    compile_id, compile_settings = node_by_class(api, "SeedVR2TorchCompileSettings")
    dit_id, dit = node_by_class(api, "SeedVR2LoadDiTModel")
    vae_id, vae = node_by_class(api, "SeedVR2LoadVAEModel")

    if components["inputs"].get("video") != [load_video_id, 0]:
        fail("GetVideoComponents.video is not wired from LoadVideo")
    if dit["inputs"].get("torch_compile_args") != [compile_id, 0]:
        fail("SeedVR2LoadDiTModel.torch_compile_args is not wired from SeedVR2TorchCompileSettings")
    if vae["inputs"].get("torch_compile_args") != [compile_id, 0]:
        fail("SeedVR2LoadVAEModel.torch_compile_args is not wired from SeedVR2TorchCompileSettings")
    if upscaler["inputs"].get("image") != [components_id, 0]:
        fail("SeedVR2VideoUpscaler.image is not wired from GetVideoComponents.images")
    if upscaler["inputs"].get("dit") != [dit_id, 0]:
        fail("SeedVR2VideoUpscaler.dit is not wired from SeedVR2LoadDiTModel")
    if upscaler["inputs"].get("vae") != [vae_id, 0]:
        fail("SeedVR2VideoUpscaler.vae is not wired from SeedVR2LoadVAEModel")
    if create_video["inputs"].get("images") != [upscaler_id, 0]:
        fail("CreateVideo.images is not wired from SeedVR2VideoUpscaler")
    if create_video["inputs"].get("audio") != [components_id, 1]:
        fail("CreateVideo.audio is not wired from GetVideoComponents.audio")
    if create_video["inputs"].get("fps") != [components_id, 2]:
        fail("CreateVideo.fps is not wired from GetVideoComponents.fps")
    if save_video["inputs"].get("video") != [create_id, 0]:
        fail("SaveVideo.video is not wired from CreateVideo")

    assert_subset(compile_settings["inputs"], EXPECTED_COMPILE, "compile")
    assert_subset(dit["inputs"], EXPECTED_DIT, "dit")
    assert_subset(vae["inputs"], EXPECTED_VAE, "vae")
    assert_subset(upscaler["inputs"], EXPECTED_UPSCALER, "upscaler")
    if contains_literal_value(api, "fixed"):
        fail("hidden UI value 'fixed' is present in API prompt")

    save_prefix = save_video["inputs"].get("filename_prefix")
    if not isinstance(save_prefix, str):
        fail(f"SaveVideo.filename_prefix must be a string, got: {save_prefix!r}")
    if not (save_prefix.startswith("video/ComfyUI") or save_prefix.startswith("video/issue_173")):
        fail(f"invalid SaveVideo prefix: {save_prefix!r}")

    result = {
        "source_workflow": str(args.source),
        "api_workflow": str(args.api),
        "forbidden_class_types": FORBIDDEN_CLASS_TYPES,
        "required_class_types": REQUIRED_CLASS_TYPES,
        "api_class_types": class_types,
        "join_image_with_alpha_present": "JoinImageWithAlpha" in class_types,
        "note_nodes_present": "Note" in class_types,
        "seedvr2_image_source": ["GetVideoComponents", "images"],
        "create_video_inputs": {
            "images": "SeedVR2VideoUpscaler",
            "audio": "GetVideoComponents.audio",
            "fps": "GetVideoComponents.fps",
        },
        "save_video_prefix": save_prefix,
        "settings_preserved": {
            "compile": EXPECTED_COMPILE,
            "dit": EXPECTED_DIT,
            "vae": EXPECTED_VAE,
            "upscaler": EXPECTED_UPSCALER,
            "hidden_fixed_absent": True,
        },
        "node_ids": {
            "LoadVideo": load_video_id,
            "GetVideoComponents": components_id,
            "SeedVR2LoadDiTModel": dit_id,
            "SeedVR2LoadVAEModel": vae_id,
            "SeedVR2TorchCompileSettings": compile_id,
            "SeedVR2VideoUpscaler": upscaler_id,
            "CreateVideo": create_id,
            "SaveVideo": save_id,
        },
        "direct_links": {
            "GetVideoComponents.video": components["inputs"]["video"],
            "SeedVR2LoadDiTModel.torch_compile_args": dit["inputs"]["torch_compile_args"],
            "SeedVR2LoadVAEModel.torch_compile_args": vae["inputs"]["torch_compile_args"],
            "SeedVR2VideoUpscaler.image": upscaler["inputs"]["image"],
            "SeedVR2VideoUpscaler.dit": upscaler["inputs"]["dit"],
            "SeedVR2VideoUpscaler.vae": upscaler["inputs"]["vae"],
            "CreateVideo.images": create_video["inputs"]["images"],
            "CreateVideo.audio": create_video["inputs"]["audio"],
            "CreateVideo.fps": create_video["inputs"]["fps"],
            "SaveVideo.video": save_video["inputs"]["video"],
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
