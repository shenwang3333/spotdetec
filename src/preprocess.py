"""Preprocessing: denoise / filter for spot detection."""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def gaussian_filter(image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Light Gaussian smoothing to reduce noise before spot detection."""
    return ndimage.gaussian_filter(image.astype(np.float64), sigma=sigma)


def preprocess_for_spots(
    image: np.ndarray,
    sigma: float = 1.0,
    clip_percentile: tuple[float, float] | None = None,
) -> np.ndarray:
    """
    Preprocess image for trackpy/spot detection: optional smoothing and optional clipping.
    Does not binarize; returns float image.
    """
    out = np.asarray(image, dtype=np.float64)
    if sigma > 0:
        out = gaussian_filter(out, sigma=sigma)
    if clip_percentile is not None:
        lo, hi = np.percentile(out, [clip_percentile[0], clip_percentile[1]])
        out = np.clip(out, lo, hi)
    return out
