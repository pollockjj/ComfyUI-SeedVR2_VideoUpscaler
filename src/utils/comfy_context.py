"""Helpers for reading ComfyUI execution context."""

from comfy_execution.utils import get_executing_context


def get_current_node_id():
    context = get_executing_context()
    return context.node_id if context is not None else None
