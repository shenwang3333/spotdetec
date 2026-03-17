"""Dual-channel: use lower as mask, upper intensity/count per lower spot, ratio distributions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class DualChannelResult:
    """Results from dual-channel (lower/upper) analysis."""
    lower_spots: np.ndarray
    upper_spots: np.ndarray
    upper_intensity_in_mask_total: float
    per_lower_upper_intensity: np.ndarray
    per_lower_upper_count: np.ndarray
    per_lower_intensity_ratio: np.ndarray
    summary: dict[str, Any]


def _circle_mask(
    shape: tuple[int, int],
    cy: float,
    cx: float,
    radius: float,
) -> np.ndarray:
    """Boolean mask of circle centered at (cy, cx) with given radius."""
    h, w = shape
    y = np.arange(h, dtype=np.float64)
    x = np.arange(w, dtype=np.float64)
    yy, xx = np.meshgrid(y, x, indexing="ij")
    return ((yy - cy) ** 2 + (xx - cx) ** 2) <= (radius ** 2)


def dual_channel_analysis(
    image_lower: np.ndarray,
    image_upper: np.ndarray,
    lower_spots: np.ndarray,
    upper_spots: np.ndarray,
    sub_mask_radius_pixels: float | None = None,
    lower_diameter: float | None = None,
) -> DualChannelResult:
    """
    For each lower spot, define a circular sub-mask; compute upper intensity sum and
    upper spot count in that sub-mask. Intensity ratio = upper_intensity / lower_mass.
    """
    shape = image_lower.shape
    n_lower = len(lower_spots)
    if n_lower == 0:
        return DualChannelResult(
            lower_spots=lower_spots,
            upper_spots=upper_spots,
            upper_intensity_in_mask_total=float(np.sum(image_upper)),
            per_lower_upper_intensity=np.array([]),
            per_lower_upper_count=np.array([]),
            per_lower_intensity_ratio=np.array([]),
            summary={
                "lower_count": 0,
                "upper_count": len(upper_spots),
                "upper_intensity_in_mask_total": float(np.sum(image_upper)),
                "intensity_ratio_mean": np.nan,
                "intensity_ratio_median": np.nan,
                "intensity_ratio_std": np.nan,
                "upper_per_lower_count_mean": np.nan,
                "upper_per_lower_count_median": np.nan,
                "upper_per_lower_count_std": np.nan,
            },
        )

    if sub_mask_radius_pixels is None and lower_diameter is not None:
        sub_mask_radius_pixels = max(2.0, lower_diameter / 2.0)
    if sub_mask_radius_pixels is None:
        sub_mask_radius_pixels = 5.0

    per_upper_intensity = np.zeros(n_lower, dtype=np.float64)
    per_upper_count = np.zeros(n_lower, dtype=np.int32)
    upper_xy = np.column_stack([upper_spots["y"], upper_spots["x"]]) if len(upper_spots) > 0 else np.zeros((0, 2))

    for i in range(n_lower):
        cy = float(lower_spots["y"][i])
        cx = float(lower_spots["x"][i])
        mask = _circle_mask(shape, cy, cx, sub_mask_radius_pixels)
        per_upper_intensity[i] = float(np.sum(image_upper[mask]))
        if len(upper_xy) > 0:
            inside = (upper_xy[:, 0] - cy) ** 2 + (upper_xy[:, 1] - cx) ** 2 <= sub_mask_radius_pixels ** 2
            per_upper_count[i] = int(np.sum(inside))

    lower_mass = np.asarray(lower_spots["mass"], dtype=np.float64)
    lower_mass_safe = np.where(lower_mass > 0, lower_mass, np.nan)
    intensity_ratio = np.where(lower_mass > 0, per_upper_intensity / lower_mass_safe, np.nan)
    valid_ratio = intensity_ratio[~np.isnan(intensity_ratio)]

    upper_intensity_in_mask_total = float(np.sum(per_upper_intensity))

    summary = {
        "lower_count": n_lower,
        "upper_count": len(upper_spots),
        "upper_intensity_in_mask_total": upper_intensity_in_mask_total,
        "intensity_ratio_mean": float(np.nanmean(valid_ratio)) if len(valid_ratio) > 0 else np.nan,
        "intensity_ratio_median": float(np.nanmedian(valid_ratio)) if len(valid_ratio) > 0 else np.nan,
        "intensity_ratio_std": float(np.nanstd(valid_ratio)) if len(valid_ratio) > 0 else np.nan,
        "upper_per_lower_count_mean": float(np.mean(per_upper_count)),
        "upper_per_lower_count_median": float(np.median(per_upper_count)),
        "upper_per_lower_count_std": float(np.std(per_upper_count)),
    }
    return DualChannelResult(
        lower_spots=lower_spots,
        upper_spots=upper_spots,
        upper_intensity_in_mask_total=upper_intensity_in_mask_total,
        per_lower_upper_intensity=per_upper_intensity,
        per_lower_upper_count=per_upper_count,
        per_lower_intensity_ratio=intensity_ratio,
        summary=summary,
    )
