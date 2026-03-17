"""Image I/O: load TIFF, multi-frame/multi-channel, batch listing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np

try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False

try:
    import imageio
    HAS_IMAGEIO = True
except ImportError:
    HAS_IMAGEIO = False


def load_image(path: Union[str, Path]) -> np.ndarray:
    """Load a single image (TIFF or other) as 2D float array."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if HAS_TIFFFILE and path.suffix.lower() in (".tif", ".tiff"):
        arr = tifffile.imread(str(path))
    elif HAS_IMAGEIO:
        arr = imageio.imread(str(path))
    else:
        if path.suffix.lower() in (".tif", ".tiff"):
            raise ImportError("Install tifffile to read TIFF files: pip install tifffile")
        raise ImportError("Install imageio to read image files: pip install imageio")

    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim == 3:
        # Multi-channel or multi-frame: return first slice for single-channel use
        arr = arr[0] if arr.shape[0] < arr.shape[-1] else arr[..., 0]
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D image, got shape {arr.shape}")
    return arr


def load_multichannel(
    path: Union[str, Path],
    channel_indices: Optional[Tuple[int, ...]] = None,
) -> Tuple[np.ndarray, ...]:
    """
    Load multi-channel image from one file.
    Returns one 2D array per channel (default: first two channels if channel_indices is None).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if HAS_TIFFFILE and path.suffix.lower() in (".tif", ".tiff"):
        arr = tifffile.imread(str(path))
    else:
        arr = load_image(path)
        return (arr,) if channel_indices is None else (arr,) * len(channel_indices)

    arr = np.asarray(arr, dtype=np.float64)
    if arr.ndim == 2:
        return (arr,)
    if arr.ndim == 3:
        if arr.shape[0] in (2, 3, 4):
            nch = arr.shape[0]
            channels = [arr[i] for i in range(nch)]
        else:
            nch = arr.shape[-1]
            channels = [arr[..., i] for i in range(nch)]
    else:
        raise ValueError(f"Unsupported image shape: {arr.shape}")

    if channel_indices is not None:
        channels = [channels[i] for i in channel_indices]
    return tuple(channels)


def load_dual_channel_files(
    path_lower: Union[str, Path],
    path_upper: Union[str, Path],
) -> Tuple[np.ndarray, np.ndarray]:
    """Load lower and upper channel from two separate files. Returns (lower, upper) 2D arrays."""
    lower = load_image(path_lower)
    upper = load_image(path_upper)
    if lower.shape != upper.shape:
        raise ValueError(
            f"Shape mismatch: lower {lower.shape} vs upper {upper.shape}. "
            "Channels must be aligned and same size."
        )
    return lower, upper


def list_image_pairs(
    folder_lower: Union[str, Path],
    folder_upper: Union[str, Path],
    extensions: Tuple[str, ...] = (".tif", ".tiff", ".png"),
) -> list[Tuple[Path, Path]]:
    """
    List pairs of images from two folders by matching filenames.
    Returns list of (path_lower, path_upper).
    """
    folder_lower = Path(folder_lower)
    folder_upper = Path(folder_upper)
    lower_files = {
        f.stem: f
        for f in folder_lower.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    }
    pairs = []
    for f in folder_upper.iterdir():
        if not f.is_file() or f.suffix.lower() not in extensions:
            continue
        stem = f.stem
        if stem in lower_files:
            pairs.append((lower_files[stem], f))
    return sorted(pairs, key=lambda p: p[0].name)


def match_pairs_by_lower(
    folder_lower: Union[str, Path],
    folder_upper: Union[str, Path],
    extensions: Tuple[str, ...] = (".tif", ".tiff", ".png"),
) -> tuple[list[Tuple[Path, Path]], list[Path]]:
    """
    Match image pairs by iterating LOWER folder and searching same-stem file in UPPER folder.

    Returns:
      - pairs: list of (lower_path, upper_path)
      - missing_upper: list of lower_path that has no matching upper file

    Matching rule:
      - same stem (filename without extension), any allowed extension in upper folder.
    """
    folder_lower = Path(folder_lower)
    folder_upper = Path(folder_upper)
    upper_map: dict[str, Path] = {}
    for f in folder_upper.iterdir():
        if f.is_file() and f.suffix.lower() in extensions:
            upper_map[f.stem] = f

    pairs: list[Tuple[Path, Path]] = []
    missing: list[Path] = []
    for f in folder_lower.iterdir():
        if not f.is_file() or f.suffix.lower() not in extensions:
            continue
        u = upper_map.get(f.stem)
        if u is None:
            missing.append(f)
        else:
            pairs.append((f, u))
    pairs = sorted(pairs, key=lambda p: p[0].name)
    missing = sorted(missing, key=lambda p: p.name)
    return pairs, missing


def list_images(
    folder: Union[str, Path],
    extensions: Tuple[str, ...] = (".tif", ".tiff", ".png"),
) -> list[Path]:
    """List image paths in folder."""
    folder = Path(folder)
    return sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in extensions],
        key=lambda f: f.name,
    )
