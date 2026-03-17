"""Single-channel statistics: size, intensity, count, area fraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SingleChannelResult:
    """Results from single-channel analysis."""
    spots: np.ndarray  # structured array with x, y, mass, size, ...
    total_count: int
    size_values: np.ndarray
    intensity_values: np.ndarray
    area_per_spot: np.ndarray
    total_spot_area: float
    fov_area_pixels: float
    area_fraction: float
    summary: dict[str, Any]


def spot_area_from_size(size: np.ndarray, pixel_scale: float = 1.0) -> np.ndarray:
    """Convert spot 'size' (radius of gyration) to approximate area in pixel^2. pi * r^2, r ~ size."""
    return np.pi * (size.astype(np.float64) ** 2) * (pixel_scale ** 2)


def analyze_single_channel(
    spots: np.ndarray,
    image_shape: tuple[int, int],
    pixel_scale: float = 1.0,
) -> SingleChannelResult:
    """
    Compute single-channel stats from detected spots.
    spots: structured array from spot_detection (x, y, mass, size, ...).
    """
    n = len(spots)
    if n == 0:
        h, w = image_shape
        fov = float(h * w) * (pixel_scale ** 2)
        return SingleChannelResult(
            spots=spots,
            total_count=0,
            size_values=np.array([]),
            intensity_values=np.array([]),
            area_per_spot=np.array([]),
            total_spot_area=0.0,
            fov_area_pixels=fov,
            area_fraction=0.0,
            summary={
                "count": 0,
                "size_mean": np.nan,
                "size_std": np.nan,
                "size_median": np.nan,
                "intensity_mean": np.nan,
                "intensity_std": np.nan,
                "intensity_median": np.nan,
                "area_fraction": 0.0,
            },
        )

    size_values = np.asarray(spots["size"], dtype=np.float64)
    intensity_values = np.asarray(spots["mass"], dtype=np.float64)
    area_per_spot = spot_area_from_size(size_values, pixel_scale)
    total_spot_area = float(np.sum(area_per_spot))
    h, w = image_shape
    fov_area_pixels = float(h * w) * (pixel_scale ** 2)
    area_fraction = total_spot_area / fov_area_pixels if fov_area_pixels > 0 else 0.0

    summary = {
        "count": n,
        "size_mean": float(np.nanmean(size_values)),
        "size_std": float(np.nanstd(size_values)),
        "size_median": float(np.nanmedian(size_values)),
        "intensity_mean": float(np.nanmean(intensity_values)),
        "intensity_std": float(np.nanstd(intensity_values)),
        "intensity_median": float(np.nanmedian(intensity_values)),
        "area_fraction": area_fraction,
        "total_spot_area": total_spot_area,
        "fov_area_pixels": fov_area_pixels,
    }
    return SingleChannelResult(
        spots=spots,
        total_count=n,
        size_values=size_values,
        intensity_values=intensity_values,
        area_per_spot=area_per_spot,
        total_spot_area=total_spot_area,
        fov_area_pixels=fov_area_pixels,
        area_fraction=area_fraction,
        summary=summary,
    )
