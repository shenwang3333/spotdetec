"""Spot detection: trackpy (primary) and optional skimage blob (LoG/DoG)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

try:
    import trackpy
    HAS_TRACKPY = True
except ImportError:
    HAS_TRACKPY = False

try:
    from skimage.feature import blob_log, blob_dog
    HAS_SKIMAGE_BLOB = True
except ImportError:
    HAS_SKIMAGE_BLOB = False


@dataclass
class SpotParams:
    """Parameters for spot detection."""
    diameter: int = 7
    minmass: float = 0.0
    separation: float | None = None
    preprocess: bool = True
    noise_size: float = 1.0
    smoothing_size: float | None = None
    threshold: float | None = None
    max_iterations: int = 10
    engine: Literal["trackpy", "log", "dog"] = "trackpy"
    # For skimage blob
    min_sigma: float = 2.0
    max_sigma: float = 5.0
    num_sigma: int = 10
    threshold_skimage: float | None = None


def _ensure_odd(n: int) -> int:
    return n if n % 2 == 1 else max(3, n + 1)


def detect_spots_trackpy(
    image: np.ndarray,
    diameter: int = 7,
    minmass: float = 0.0,
    separation: float | None = None,
    preprocess: bool = True,
    noise_size: float = 1.0,
    smoothing_size: float | None = None,
    threshold: float | None = None,
    max_iterations: int = 10,
) -> np.ndarray:
    """
    Detect spots using trackpy.locate. Returns structured array with columns
    x, y, mass, size, signal, raw_mass, ep, frame (and possibly ecc).
    """
    if not HAS_TRACKPY:
        raise ImportError("trackpy is required: pip install trackpy")
    diameter = _ensure_odd(diameter)
    if separation is None:
        separation = diameter
    if smoothing_size is None:
        smoothing_size = diameter
    df = trackpy.locate(
        image,
        diameter=diameter,
        minmass=minmass,
        separation=separation,
        preprocess=preprocess,
        noise_size=noise_size,
        smoothing_size=smoothing_size,
        threshold=threshold,
        max_iterations=max_iterations,
    )
    if df is None or len(df) == 0:
        return _empty_spots_array()
    return df.to_records(index=False)


def detect_spots_blob_log(
    image: np.ndarray,
    min_sigma: float = 2.0,
    max_sigma: float = 5.0,
    num_sigma: int = 10,
    threshold: float | None = None,
) -> np.ndarray:
    """
    Detect bright blobs using skimage blob_log. Returns array with x, y, mass, size, etc.
    blob_log returns (row, col, sigma); we map to (x=col, y=row) and approximate mass/size.
    """
    if not HAS_SKIMAGE_BLOB:
        raise ImportError("scikit-image is required: pip install scikit-image")
    if threshold is None:
        threshold = 0.1 * (np.max(image) - np.min(image)) + np.min(image) if image.size else 0
    blobs = blob_log(image, min_sigma=min_sigma, max_sigma=max_sigma, num_sigma=num_sigma, threshold=threshold)
    if len(blobs) == 0:
        return _empty_spots_array()
    # blobs: (y, x, sigma)
    dtype = [
        ("x", np.float64),
        ("y", np.float64),
        ("mass", np.float64),
        ("size", np.float64),
        ("signal", np.float64),
        ("raw_mass", np.float64),
        ("ep", np.float64),
        ("frame", np.int32),
    ]
    out = np.zeros(len(blobs), dtype=dtype)
    out["y"] = blobs[:, 0]
    out["x"] = blobs[:, 1]
    sigma = blobs[:, 2]
    out["size"] = sigma * np.sqrt(2)
    r = out["size"]
    for i, (yi, xi, s) in enumerate(blobs):
        y0, y1 = max(0, int(yi - 3 * s)), min(image.shape[0], int(yi + 3 * s) + 1)
        x0, x1 = max(0, int(xi - 3 * s)), min(image.shape[1], int(xi + 3 * s) + 1)
        patch = image[y0:y1, x0:x1]
        out["mass"][i] = out["raw_mass"][i] = float(np.sum(patch))
        out["signal"][i] = float(image[int(yi), int(xi)]) if 0 <= int(yi) < image.shape[0] and 0 <= int(xi) < image.shape[1] else 0
    out["ep"] = 0
    out["frame"] = 0
    return out


def detect_spots_blob_dog(
    image: np.ndarray,
    min_sigma: float = 2.0,
    max_sigma: float = 5.0,
    num_sigma: int = 10,
    threshold: float | None = None,
) -> np.ndarray:
    """Detect blobs using blob_dog; same interface as blob_log."""
    if not HAS_SKIMAGE_BLOB:
        raise ImportError("scikit-image is required: pip install scikit-image")
    if threshold is None:
        threshold = 0.1 * (np.max(image) - np.min(image)) + np.min(image) if image.size else 0
    blobs = blob_dog(image, min_sigma=min_sigma, max_sigma=max_sigma, threshold=threshold)
    if len(blobs) == 0:
        return _empty_spots_array()
    dtype = [
        ("x", np.float64),
        ("y", np.float64),
        ("mass", np.float64),
        ("size", np.float64),
        ("signal", np.float64),
        ("raw_mass", np.float64),
        ("ep", np.float64),
        ("frame", np.int32),
    ]
    out = np.zeros(len(blobs), dtype=dtype)
    out["y"] = blobs[:, 0]
    out["x"] = blobs[:, 1]
    sigma = blobs[:, 2]
    out["size"] = sigma * np.sqrt(2)
    for i, (yi, xi, s) in enumerate(blobs):
        y0, y1 = max(0, int(yi - 3 * s)), min(image.shape[0], int(yi + 3 * s) + 1)
        x0, x1 = max(0, int(xi - 3 * s)), min(image.shape[1], int(xi + 3 * s) + 1)
        patch = image[y0:y1, x0:x1]
        out["mass"][i] = out["raw_mass"][i] = float(np.sum(patch))
        out["signal"][i] = float(image[int(yi), int(xi)]) if 0 <= int(yi) < image.shape[0] and 0 <= int(xi) < image.shape[1] else 0
    out["ep"] = 0
    out["frame"] = 0
    return out


def _empty_spots_array() -> np.ndarray:
    dtype = [
        ("x", np.float64),
        ("y", np.float64),
        ("mass", np.float64),
        ("size", np.float64),
        ("signal", np.float64),
        ("raw_mass", np.float64),
        ("ep", np.float64),
        ("frame", np.int32),
    ]
    return np.array([], dtype=dtype)


def detect_spots(image: np.ndarray, params: SpotParams) -> np.ndarray:
    """Unified spot detection from SpotParams."""
    if params.engine == "trackpy":
        return detect_spots_trackpy(
            image,
            diameter=params.diameter,
            minmass=params.minmass,
            separation=params.separation,
            preprocess=params.preprocess,
            noise_size=params.noise_size,
            smoothing_size=params.smoothing_size,
            threshold=params.threshold,
            max_iterations=params.max_iterations,
        )
    if params.engine == "log":
        return detect_spots_blob_log(
            image,
            min_sigma=params.min_sigma,
            max_sigma=params.max_sigma,
            num_sigma=params.num_sigma,
            threshold=params.threshold_skimage,
        )
    if params.engine == "dog":
        return detect_spots_blob_dog(
            image,
            min_sigma=params.min_sigma,
            max_sigma=params.max_sigma,
            num_sigma=params.num_sigma,
            threshold=params.threshold_skimage,
        )
    raise ValueError(f"Unknown engine: {params.engine}")
