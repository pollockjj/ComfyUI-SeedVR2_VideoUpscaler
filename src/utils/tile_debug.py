VALID_TILE_DEBUG_MODES = frozenset({"false", "encode", "decode"})
TILE_DEBUG_ERROR = "tile_debug must be one of 'false', 'encode', or 'decode'"


def normalize_tile_debug(value: str | bool | None) -> str:
    if value is False or value is None:
        return "false"
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in VALID_TILE_DEBUG_MODES:
            return normalized
        raise ValueError(f"{TILE_DEBUG_ERROR}, got {value!r}")
    raise TypeError(f"{TILE_DEBUG_ERROR}, got {value!r}")
