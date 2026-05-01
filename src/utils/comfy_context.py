"""Helpers for reading ComfyUI execution context."""

from comfy_execution.utils import get_executing_context


def get_current_node_id():
    context = get_executing_context()
    return getattr(context, "node_id", None) if context is not None else None


def require_node_id_for_cache(cache_model: bool, model_kind: str):
    node_id = get_current_node_id()
    if cache_model and node_id is None:
        raise ValueError(
            f"Model caching (cache_model=True) for {model_kind} requires an active "
            "ComfyUI execution context with a node_id. Disable cache_model or run "
            "the node through ComfyUI execution so cached models cannot share an "
            "unresolved node_id."
        )
    return node_id
