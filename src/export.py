"""Export: CSV and distribution plots."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .single_channel import SingleChannelResult
    from .dual_channel import DualChannelResult

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def export_batch_summary(rows: list[dict[str, Any]], path: str | Path) -> None:
    """Export a batch-level summary table (one row per image/pair)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if len(rows) == 0:
        # still create an empty file with at least a header
        if HAS_PANDAS:
            pd.DataFrame([]).to_csv(path, index=False)
        else:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["empty"])
        return

    if HAS_PANDAS:
        pd.DataFrame(rows).to_csv(path, index=False)
        return

    # manual CSV (stable column order: union of keys, with common fields first)
    import csv

    common_first = [
        "mode",
        "file",
        "file_lower",
        "file_upper",
        "image_shape",
        "spot_engine",
        "diameter",
        "minmass",
        "separation",
        "preprocess_sigma",
    ]
    keys = set().union(*[set(r.keys()) for r in rows])
    ordered = [k for k in common_first if k in keys] + sorted([k for k in keys if k not in common_first])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ordered)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def export_single_channel_csv(result: "SingleChannelResult", path: str | Path) -> None:
    """Export single-channel spots and summary to CSV."""
    path = Path(path)
    if not HAS_PANDAS:
        _export_single_csv_manual(result, path)
        return
    df = pd.DataFrame({
        "x": result.spots["x"],
        "y": result.spots["y"],
        "mass": result.spots["mass"],
        "size": result.spots["size"],
        "signal": result.spots["signal"] if "signal" in result.spots.dtype.names else result.spots["mass"],
        "area": result.area_per_spot,
    })
    df.to_csv(path, index=False)
    summary_path = path.parent / (path.stem + "_summary.csv")
    pd.DataFrame([result.summary]).to_csv(summary_path, index=False)


def _export_single_csv_manual(result: "SingleChannelResult", path: Path) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        names = list(result.spots.dtype.names) + ["area"]
        w.writerow(names)
        for i in range(len(result.spots)):
            row = [result.spots[n][i] for n in result.spots.dtype.names] + [result.area_per_spot[i]]
            w.writerow(row)


def export_dual_channel_csv(result: "DualChannelResult", path: str | Path) -> None:
    """Export dual-channel per-lower metrics and summary to CSV."""
    path = Path(path)
    if not HAS_PANDAS:
        _export_dual_csv_manual(result, path)
        return
    df = pd.DataFrame({
        "lower_x": result.lower_spots["x"],
        "lower_y": result.lower_spots["y"],
        "lower_mass": result.lower_spots["mass"],
        "lower_size": result.lower_spots["size"],
        "upper_intensity_in_submask": result.per_lower_upper_intensity,
        "upper_count_in_submask": result.per_lower_upper_count,
        "intensity_ratio_upper_over_lower": result.per_lower_intensity_ratio,
    })
    df.to_csv(path, index=False)
    summary_path = path.parent / (path.stem + "_summary.csv")
    pd.DataFrame([result.summary]).to_csv(summary_path, index=False)


def _export_dual_csv_manual(result: "DualChannelResult", path: Path) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "lower_x", "lower_y", "lower_mass", "lower_size",
            "upper_intensity_in_submask", "upper_count_in_submask", "intensity_ratio_upper_over_lower",
        ])
        for i in range(len(result.lower_spots)):
            w.writerow([
                result.lower_spots["x"][i], result.lower_spots["y"][i],
                result.lower_spots["mass"][i], result.lower_spots["size"][i],
                result.per_lower_upper_intensity[i], result.per_lower_upper_count[i],
                result.per_lower_intensity_ratio[i],
            ])


def plot_single_channel_distributions(
    result: "SingleChannelResult",
    output_dir: str | Path,
    prefix: str = "single",
) -> list[Path]:
    """Save size and intensity distribution histograms. Returns list of saved paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    if not HAS_MATPLOTLIB:
        return saved
    if len(result.size_values) == 0:
        return saved
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].hist(result.size_values, bins=min(50, max(10, len(result.size_values) // 5)), color="steelblue", edgecolor="black", alpha=0.7)
    axes[0].set_xlabel("Size (radius of gyration)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Size distribution")
    axes[1].hist(result.intensity_values, bins=min(50, max(10, len(result.intensity_values) // 5)), color="coral", edgecolor="black", alpha=0.7)
    axes[1].set_xlabel("Intensity (mass)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Intensity distribution")
    plt.tight_layout()
    p = output_dir / f"{prefix}_distributions.png"
    plt.savefig(p, dpi=150)
    plt.close()
    saved.append(p)
    return saved


def plot_dual_channel_distributions(
    result: "DualChannelResult",
    output_dir: str | Path,
    prefix: str = "dual",
) -> list[Path]:
    """Save intensity-ratio and upper-count-per-lower distributions."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    if not HAS_MATPLOTLIB:
        return saved
    if len(result.lower_spots) == 0:
        return saved
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    valid_ratio = result.per_lower_intensity_ratio[~np.isnan(result.per_lower_intensity_ratio)]
    if len(valid_ratio) > 0:
        axes[0].hist(valid_ratio, bins=min(50, max(10, len(valid_ratio) // 3)), color="green", edgecolor="black", alpha=0.7)
    axes[0].set_xlabel("Intensity ratio (upper / lower)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Intensity ratio distribution")
    axes[1].hist(result.per_lower_upper_count, bins=range(int(result.per_lower_upper_count.max()) + 2) if result.per_lower_upper_count.size else [0], color="purple", edgecolor="black", alpha=0.7)
    axes[1].set_xlabel("Upper liposome count per lower")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Upper-per-lower count distribution")
    plt.tight_layout()
    p = output_dir / f"{prefix}_distributions.png"
    plt.savefig(p, dpi=150)
    plt.close()
    saved.append(p)
    return saved
