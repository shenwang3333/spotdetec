"""Pipeline: run single or dual-channel analysis with optional preprocessing and export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from . import io, preprocess
from .dual_channel import dual_channel_analysis, DualChannelResult
from .export import (
    export_dual_channel_csv,
    export_single_channel_csv,
    export_batch_summary,
    plot_dual_channel_distributions,
    plot_single_channel_distributions,
)
from .single_channel import analyze_single_channel, SingleChannelResult
from .spot_detection import SpotParams, detect_spots


@dataclass
class PipelineParams:
    """Parameters for the full pipeline."""
    spot_params: SpotParams
    preprocess_sigma: float = 1.0
    sub_mask_radius_pixels: float | None = None
    pixel_scale: float = 1.0


def run_single_channel(
    image: np.ndarray,
    params: PipelineParams,
) -> SingleChannelResult:
    """Run single-channel analysis: preprocess -> detect -> stats."""
    if params.preprocess_sigma > 0:
        image = preprocess.preprocess_for_spots(image, sigma=params.preprocess_sigma)
    spots = detect_spots(image, params.spot_params)
    return analyze_single_channel(spots, image.shape, pixel_scale=params.pixel_scale)


def run_dual_channel(
    image_lower: np.ndarray,
    image_upper: np.ndarray,
    params: PipelineParams,
) -> DualChannelResult:
    """Run dual-channel analysis: preprocess both -> detect both -> correlate."""
    if params.preprocess_sigma > 0:
        image_lower = preprocess.preprocess_for_spots(image_lower, sigma=params.preprocess_sigma)
        image_upper = preprocess.preprocess_for_spots(image_upper, sigma=params.preprocess_sigma)
    lower_spots = detect_spots(image_lower, params.spot_params)
    upper_spots = detect_spots(image_upper, params.spot_params)
    radius = params.sub_mask_radius_pixels
    if radius is None:
        radius = max(3.0, params.spot_params.diameter / 2.0)
    return dual_channel_analysis(
        image_lower,
        image_upper,
        lower_spots,
        upper_spots,
        sub_mask_radius_pixels=radius,
        lower_diameter=float(params.spot_params.diameter),
    )


def process_single_file(
    input_path: Path,
    output_dir: Path,
    params: PipelineParams,
    mode: str = "single",
    path_upper: Path | None = None,
    channels_from_one: tuple[int, int] | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> SingleChannelResult | DualChannelResult:
    """
    Process one image (single) or one pair (dual). Export CSV and plots to output_dir.
    mode: "single" | "dual"
    channels_from_one: for dual mode, (lower_ch, upper_ch) to load from single file; else use path_upper.
    """
    def log(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    if mode == "single":
        log(f"Loading {input_path.name}")
        image = io.load_image(input_path)
        log("Running single-channel analysis")
        result = run_single_channel(image, params)
        out_csv = output_dir / (input_path.stem + "_single.csv")
        export_single_channel_csv(result, out_csv)
        plot_single_channel_distributions(result, output_dir, prefix=input_path.stem + "_single")
        log(f"Saved {out_csv.name}")
        return result

    if mode == "dual":
        if channels_from_one is not None:
            log(f"Loading {input_path.name} (channels {channels_from_one[0]}, {channels_from_one[1]})")
            chs = io.load_multichannel(input_path, channel_indices=channels_from_one)
            image_lower, image_upper = chs[0], chs[1]
        elif path_upper is not None:
            log(f"Loading {input_path.name}, {path_upper.name}")
            image_lower, image_upper = io.load_dual_channel_files(input_path, path_upper)
        else:
            raise ValueError("For dual mode provide path_upper or channels_from_one")
        log("Running dual-channel analysis")
        result = run_dual_channel(image_lower, image_upper, params)
        out_csv = output_dir / (input_path.stem + "_dual.csv")
        export_dual_channel_csv(result, out_csv)
        plot_dual_channel_distributions(result, output_dir, prefix=input_path.stem + "_dual")
        log(f"Saved {out_csv.name}")
        return result

    raise ValueError(f"Unknown mode: {mode}")


def process_batch(
    input_paths: list[tuple[Path, Path | None]],
    output_dir: Path,
    params: PipelineParams,
    mode: str,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[SingleChannelResult | DualChannelResult]:
    """
    input_paths: list of (path_lower_or_single, path_upper_or_None).
    For single mode, path_upper is None. For dual, both are set.
    """
    results: list[SingleChannelResult | DualChannelResult] = []
    summary_rows: list[dict] = []
    n = len(input_paths)
    for i, (p1, p2) in enumerate(input_paths):
        if progress_callback:
            progress_callback(i, n, p1.name)
        result = process_single_file(
            p1,
            output_dir,
            params,
            mode=mode,
            path_upper=p2,
            progress_callback=lambda msg: progress_callback(i, n, msg) if progress_callback else None,
        )
        results.append(result)

        base = {
            "mode": mode,
            "file": p1.name if p2 is None else f"{p1.name} + {p2.name}",
            "file_lower": p1.name,
            "file_upper": p2.name if p2 is not None else "",
            "image_shape": getattr(result, "spots", getattr(result, "lower_spots", np.array([]))).shape,
            "spot_engine": params.spot_params.engine,
            "diameter": params.spot_params.diameter,
            "minmass": params.spot_params.minmass,
            "separation": params.spot_params.separation if params.spot_params.separation is not None else "",
            "preprocess_sigma": params.preprocess_sigma,
        }
        # Merge analysis summary (already numeric / serializable)
        row = dict(base)
        if hasattr(result, "summary"):
            row.update(result.summary)
        summary_rows.append(row)

    # Write one batch summary CSV for convenience
    out_name = f"batch_summary_{mode}.csv"
    export_batch_summary(summary_rows, output_dir / out_name)
    return results
