"""
Shared constants and utilities for SeedVR2
Only includes constants actually used in the codebase
"""

# Version information
__version__ = "2.5.24"

import os
import warnings
import re
from typing import Any, Optional

# Model folder names
SEEDVR2_FOLDER_NAME = "SEEDVR2" # Physical folder name on disk
SEEDVR2_MODEL_TYPE = "seedvr2" # Model type identifier for ComfyUI

# Supported model file formats
SUPPORTED_MODEL_EXTENSIONS = {'.safetensors', '.gguf'}

# GGUF Quantization Constants
QK_K = 256
K_SCALE_SIZE = 12
GGUF_BLOCK_SIZE = 32
GGUF_TYPE_SIZE = 64

# Download configuration
HUGGINGFACE_BASE_URL = "https://huggingface.co/{repo}/resolve/main/{filename}"
DOWNLOAD_CHUNK_SIZE = 8192 * 1024  # 8MB chunks for hash calculation
DOWNLOAD_MAX_RETRIES = 3
DOWNLOAD_RETRY_DELAY = 2  # seconds

def get_script_directory() -> str:
    """Get the root script directory path (3 levels up from this file)"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_base_cache_dir() -> str:
    """
    Get the default model cache directory path.
    
    Returns the path without creating the directory.
    
    Returns:
        str: Path to default cache directory
    """
    try:
        import folder_paths  # Only works if ComfyUI is available
        cache_dir = os.path.join(folder_paths.models_dir, SEEDVR2_FOLDER_NAME)
        folder_paths.add_model_folder_path(SEEDVR2_MODEL_TYPE, cache_dir)
    except:
        cache_dir = f"./models/{SEEDVR2_FOLDER_NAME}"
    
    return cache_dir


def _collect_base_paths_from_yaml_node(node: Any) -> list[str]:
    if isinstance(node, dict):
        paths = []
        for key, value in node.items():
            if key == "base_path" and isinstance(value, str) and value.strip():
                paths.append(os.path.expanduser(value.strip()))
            paths.extend(_collect_base_paths_from_yaml_node(value))
        return paths
    if isinstance(node, list):
        paths = []
        for item in node:
            paths.extend(_collect_base_paths_from_yaml_node(item))
        return paths
    return []


def _fallback_extra_model_base_paths(text: str) -> list[str]:
    base_path_pattern = re.compile(r"^\s*(?:-\s*)?base_path\s*:\s*(?P<value>.+?)\s*$")
    paths = []
    for line in text.splitlines():
        match = base_path_pattern.match(line)
        if not match:
            continue
        value = match.group("value").split("#", 1)[0].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if value:
            paths.append(os.path.expanduser(value))
    return paths


def _extra_model_seedvr2_paths(extra_model_paths: str) -> list[str]:
    with open(extra_model_paths, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        import yaml
    except ImportError:
        base_paths = _fallback_extra_model_base_paths(text)
    else:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            base_paths = _fallback_extra_model_base_paths(text)
        else:
            base_paths = _collect_base_paths_from_yaml_node(data)
    return [os.path.join(base_path, "models", SEEDVR2_FOLDER_NAME) for base_path in base_paths]


def get_all_model_paths() -> list:
    """Get all registered model paths including those from extra_model_paths.yaml (case-insensitive)"""
    try:
        import folder_paths
        # Ensure default path is registered first
        get_base_cache_dir()
        
        # Case-insensitive lookup: search through all registered folder types
        # This handles any case variation users might use in extra_model_paths.yaml
        all_paths = []
        target_lower = SEEDVR2_MODEL_TYPE.lower()
        models_roots = set()
        
        # folder_paths.folder_names_and_paths is the underlying dict: {type: ([paths], extensions)}
        if hasattr(folder_paths, 'folder_names_and_paths'):
            for folder_type, (paths, _) in folder_paths.folder_names_and_paths.items():
                if folder_type.lower() == target_lower:
                    all_paths.extend(paths)
                for path in paths:
                    models_root = os.path.dirname(path)
                    if os.path.basename(models_root).lower() == "models":
                        models_roots.add(os.path.normpath(models_root))
            for models_root in sorted(models_roots, key=str.lower):
                all_paths.append(os.path.join(models_root, SEEDVR2_FOLDER_NAME))

        models_dir = getattr(folder_paths, 'models_dir', None)
        if models_dir:
            extra_model_paths = os.path.join(os.path.dirname(models_dir), "extra_model_paths.yaml")
            if os.path.exists(extra_model_paths):
                all_paths.extend(_extra_model_seedvr2_paths(extra_model_paths))
        
        # Remove duplicates while preserving order (os.path.normpath handles Windows/Linux path differences)
        seen = set()
        unique_paths = []
        for path in all_paths:
            normalized = os.path.normpath(path.lower())
            if normalized not in seen:
                seen.add(normalized)
                unique_paths.append(path)
        
        return unique_paths if unique_paths else [get_base_cache_dir()]
    except:
        return [get_base_cache_dir()]


def get_all_model_files() -> dict:
    """
    Get a mapping of all model files to their full paths across all registered directories.
    
    Returns:
        dict: Mapping of filename -> full path for all discovered model files
    """
    model_files = {}
    all_paths = get_all_model_paths()
    
    for path in all_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if is_supported_model_file(file):
                    # Only keep first occurrence of each file (priority order)
                    if file not in model_files:
                        model_files[file] = os.path.join(path, file)
    
    return model_files


def find_model_file(filename: str, fallback_dir: Optional[str] = None) -> str:
    """
    Find a model file in any registered path.
    
    Args:
        filename: Name of the model file to find
        fallback_dir: Directory to use if file not found in any registered path
        
    Returns:
        str: Full path to the model file
    """
    # Get all model files
    model_files = get_all_model_files()
    
    # Return path if found
    if filename in model_files:
        return model_files[filename]
    
    # Fallback to specified directory or base cache dir
    if fallback_dir:
        return os.path.join(fallback_dir, filename)
    else:
        return os.path.join(get_base_cache_dir(), filename)


def get_validation_cache_path(cache_dir: Optional[str] = None) -> str:
    """
    Get path to model validation cache file.
    
    Args:
        cache_dir: Optional directory for cache file. If None, uses default base cache dir.
        
    Returns:
        Full path to validation cache JSON file
    """
    if cache_dir is None:
        cache_dir = get_base_cache_dir()
    return os.path.join(cache_dir, ".validation_cache.json")


def is_supported_model_file(filename: str) -> bool:
    """Check if a file has a supported model extension"""
    return any(filename.endswith(ext) for ext in SUPPORTED_MODEL_EXTENSIONS)


def suppress_tensor_warnings() -> None:
    """
    Suppress common tensor conversion and numpy array warnings that are expected behavior
    when working with GGUF tensors and numpy arrays.
    """
    warnings.filterwarnings("ignore", message="To copy construct from a tensor", category=UserWarning)
    warnings.filterwarnings("ignore", message="The given NumPy array is not writable", category=UserWarning)
