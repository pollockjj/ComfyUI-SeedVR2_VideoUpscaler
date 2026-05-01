"""
Public SeedVR2 latent boundary nodes.

These nodes expose the existing Numz phase split so another node can replace
the DiT upscaling phase while keeping Numz tiled VAE encode/decode.
"""

from typing import Any, Dict, Optional

import torch
from comfy_api.latest import io

from ..core.generation_phases import (
    decode_all_batches,
    encode_all_batches,
    postprocess_all_batches,
)
from ..core.generation_utils import (
    compute_generation_info,
    log_generation_start,
    prepare_runner,
    setup_generation_context,
)
from ..optimization.memory_manager import (
    cleanup_text_embeddings,
    complete_cleanup,
    get_device_list,
)
from ..utils.constants import get_base_cache_dir
from ..utils.debug import Debug
from ..utils.model_registry import DEFAULT_DIT

try:
    from comfy.utils import ProgressBar
except ImportError:
    ProgressBar = None


def _make_progress_callback(pbar: Optional["ProgressBar"], phase_offset: float, phase_weight: float):
    def progress_callback(current_step: int, total_steps: int, current_frames: int, phase_name: str) -> None:
        if pbar is None:
            return
        phase_progress = (current_step / total_steps) if total_steps > 0 else 0
        progress_value = int((phase_offset + phase_progress * phase_weight) * 100)
        pbar.update_absolute(progress_value, 100)

    return progress_callback


def _apply_model_config_from_vae(vae: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx["vae_device"] = torch.device(vae["device"])
    vae_offload_str = vae.get("offload_device", "none")
    ctx["vae_offload_device"] = torch.device(vae_offload_str) if vae_offload_str != "none" else None
    return ctx


def _prepare_vae_runner(
    vae: Dict[str, Any],
    ctx: Dict[str, Any],
    debug: Debug,
):
    vae_model = vae["model"]
    return prepare_runner(
        dit_model=DEFAULT_DIT,
        vae_model=vae_model,
        model_dir=get_base_cache_dir(),
        debug=debug,
        ctx=ctx,
        dit_cache=False,
        vae_cache=vae.get("cache_model", False),
        dit_id=None,
        vae_id=vae.get("node_id"),
        block_swap_config=None,
        encode_tiled=vae.get("encode_tiled", False),
        encode_tile_size=(vae.get("encode_tile_size", 512), vae.get("encode_tile_size", 512)),
        encode_tile_overlap=(vae.get("encode_tile_overlap", 64), vae.get("encode_tile_overlap", 64)),
        decode_tiled=vae.get("decode_tiled", False),
        decode_tile_size=(vae.get("decode_tile_size", 512), vae.get("decode_tile_size", 512)),
        decode_tile_overlap=(vae.get("decode_tile_overlap", 64), vae.get("decode_tile_overlap", 64)),
        tile_debug=vae.get("tile_debug", "false"),
        attention_mode="sdpa",
        torch_compile_args_dit=None,
        torch_compile_args_vae=vae.get("torch_compile_args"),
    )


class SeedVR2VAEEncode(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeedVR2VAEEncode",
            display_name="SeedVR2 VAE Encode",
            category="SEEDVR2",
            inputs=[
                io.Image.Input("image"),
                io.Custom("SEEDVR2_VAE").Input("vae"),
                io.Int.Input("seed", default=42, min=0, max=2**32 - 1, step=1),
                io.Int.Input("resolution", default=1080, min=16, max=16384, step=2),
                io.Int.Input("max_resolution", default=0, min=0, max=16384, step=2),
                io.Int.Input("batch_size", default=5, min=1, max=16384, step=4),
                io.Boolean.Input("uniform_batch_size", default=False),
                io.Int.Input("temporal_overlap", default=0, min=0, max=16, step=1, optional=True),
                io.Int.Input("prepend_frames", default=0, min=0, max=32, step=1, optional=True),
                io.Combo.Input(
                    "color_correction",
                    options=["lab", "wavelet", "wavelet_adaptive", "hsv", "adain", "none"],
                    default="lab",
                ),
                io.Float.Input("input_noise_scale", default=0.0, min=0.0, max=1.0, step=0.001, optional=True),
                io.Combo.Input(
                    "offload_device",
                    options=get_device_list(include_none=True, include_cpu=True),
                    default="cpu",
                    optional=True,
                ),
                io.Boolean.Input("enable_debug", default=False, optional=True),
            ],
            outputs=[io.Custom("SEEDVR2_LATENTS").Output()],
        )

    @classmethod
    def execute(
        cls,
        image: torch.Tensor,
        vae: Dict[str, Any],
        seed: int,
        resolution: int = 1080,
        max_resolution: int = 0,
        batch_size: int = 5,
        uniform_batch_size: bool = False,
        temporal_overlap: int = 0,
        prepend_frames: int = 0,
        color_correction: str = "lab",
        input_noise_scale: float = 0.0,
        offload_device: str = "cpu",
        enable_debug: bool = False,
    ) -> io.NodeOutput:
        debug = Debug(enabled=enable_debug)
        pbar = ProgressBar(100) if ProgressBar is not None else None
        tensor_offload_device = torch.device(offload_device) if offload_device != "none" else None
        vae_device = torch.device(vae["device"])
        vae_offload = vae.get("offload_device", "none")
        vae_offload_device = torch.device(vae_offload) if vae_offload != "none" else None

        ctx = setup_generation_context(
            dit_device=vae_device,
            vae_device=vae_device,
            dit_offload_device=None,
            vae_offload_device=vae_offload_device,
            tensor_offload_device=tensor_offload_device,
            debug=debug,
        )
        runner = None
        try:
            runner, cache_context = _prepare_vae_runner(vae, ctx, debug)
            ctx["cache_context"] = cache_context
            image, gen_info = compute_generation_info(
                ctx=ctx,
                images=image,
                resolution=resolution,
                max_resolution=max_resolution,
                batch_size=batch_size,
                uniform_batch_size=uniform_batch_size,
                seed=seed,
                prepend_frames=prepend_frames,
                temporal_overlap=temporal_overlap,
                debug=debug,
            )
            log_generation_start(gen_info, debug)
            ctx = encode_all_batches(
                runner,
                ctx=ctx,
                images=image,
                debug=debug,
                batch_size=batch_size,
                uniform_batch_size=uniform_batch_size,
                seed=seed,
                progress_callback=_make_progress_callback(pbar, 0.0, 1.0),
                temporal_overlap=temporal_overlap,
                resolution=resolution,
                max_resolution=max_resolution,
                input_noise_scale=input_noise_scale,
                color_correction=color_correction,
            )
            cleanup_text_embeddings(ctx, debug)
            payload = {
                "stage": "encoded",
                "ctx": ctx,
                "all_latents": ctx["all_latents"],
                "color_correction": color_correction,
                "prepend_frames": prepend_frames,
                "temporal_overlap": temporal_overlap,
                "batch_size": batch_size,
            }
            return io.NodeOutput(payload)
        finally:
            if runner is not None:
                complete_cleanup(
                    runner=runner,
                    debug=debug,
                    dit_cache=False,
                    vae_cache=vae.get("cache_model", False),
                )


class SeedVR2VAEDecode(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SeedVR2VAEDecode",
            display_name="SeedVR2 VAE Decode",
            category="SEEDVR2",
            inputs=[
                io.Custom("SEEDVR2_LATENTS").Input("latents"),
                io.Custom("SEEDVR2_VAE").Input("vae"),
                io.Combo.Input(
                    "offload_device",
                    options=get_device_list(include_none=True, include_cpu=True),
                    default="cpu",
                    optional=True,
                ),
                io.Boolean.Input("enable_debug", default=False, optional=True),
            ],
            outputs=[io.Image.Output()],
        )

    @classmethod
    def execute(
        cls,
        latents: Dict[str, Any],
        vae: Dict[str, Any],
        offload_device: str = "cpu",
        enable_debug: bool = False,
    ) -> io.NodeOutput:
        if latents.get("stage") != "upscaled":
            raise ValueError(f"Expected SEEDVR2_LATENTS stage='upscaled', got {latents.get('stage')!r}")
        ctx = latents.get("ctx")
        if not isinstance(ctx, dict):
            raise ValueError("SEEDVR2_LATENTS payload is missing ctx")
        if "all_upscaled_latents" not in ctx:
            ctx["all_upscaled_latents"] = latents.get("all_upscaled_latents")
        if not ctx.get("all_upscaled_latents"):
            raise ValueError("SEEDVR2_LATENTS payload has no all_upscaled_latents")

        debug = Debug(enabled=enable_debug)
        pbar = ProgressBar(100) if ProgressBar is not None else None
        ctx = _apply_model_config_from_vae(vae, ctx)
        ctx["tensor_offload_device"] = torch.device(offload_device) if offload_device != "none" else None
        runner = None
        try:
            runner, cache_context = _prepare_vae_runner(vae, ctx, debug)
            ctx["cache_context"] = cache_context
            ctx = decode_all_batches(
                runner,
                ctx=ctx,
                debug=debug,
                progress_callback=_make_progress_callback(pbar, 0.0, 0.6),
                cache_model=vae.get("cache_model", False),
            )
            ctx = postprocess_all_batches(
                ctx=ctx,
                debug=debug,
                progress_callback=_make_progress_callback(pbar, 0.6, 0.4),
                color_correction=latents.get("color_correction", "lab"),
                prepend_frames=latents.get("prepend_frames", 0),
                temporal_overlap=latents.get("temporal_overlap", 0),
                batch_size=latents.get("batch_size", 5),
            )
            sample = ctx["final_video"]
            if torch.is_tensor(sample):
                if sample.is_cuda or sample.is_mps:
                    sample = sample.cpu()
                if sample.dtype != torch.float32:
                    sample = sample.to(torch.float32)
            return io.NodeOutput(sample)
        finally:
            if runner is not None:
                complete_cleanup(
                    runner=runner,
                    debug=debug,
                    dit_cache=False,
                    vae_cache=vae.get("cache_model", False),
                )
