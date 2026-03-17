"""Preview dialog: run spot detection on one image and visualize detected spots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from src import io, preprocess
from src.pipeline import PipelineParams
from src.spot_detection import detect_spots


def _norm_for_display(img: np.ndarray, p_lo: float = 1.0, p_hi: float = 99.9) -> tuple[float, float]:
    if img.size == 0:
        return 0.0, 1.0
    lo = float(np.percentile(img, p_lo))
    hi = float(np.percentile(img, p_hi))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo = float(np.min(img))
        hi = float(np.max(img)) if float(np.max(img)) > lo else lo + 1.0
    return lo, hi


def _spot_mass_stats(spots: np.ndarray) -> str:
    if len(spots) == 0:
        return "mass: —"
    m = np.asarray(spots["mass"], dtype=np.float64)
    return f"mass mean={np.mean(m):.2f}, median={np.median(m):.2f}, min={np.min(m):.2f}, max={np.max(m):.2f}"


class _ImageCanvas(FigureCanvas):
    def __init__(self, parent: QWidget | None = None) -> None:
        fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def show_image_with_spots(self, image: np.ndarray, spots: np.ndarray, radius: float) -> None:
        self.ax.clear()
        vmin, vmax = _norm_for_display(image)
        self.ax.imshow(image, cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")
        self.ax.set_axis_off()
        if len(spots) > 0:
            for x, y in zip(spots["x"], spots["y"]):
                self.ax.add_patch(Circle((float(x), float(y)), radius=radius, fill=False, lw=1.0, ec="lime"))
        self.ax.set_title(f"Detected spots: {len(spots)}")
        self.figure.tight_layout()
        self.draw()


class PreviewDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("参数预览：spots 识别可视化")
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        self.info = QLabel("—")
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.info)

        self.tabs = QTabWidget()
        self.canvas_raw = _ImageCanvas()
        self.canvas_pre = _ImageCanvas()
        w1 = QWidget()
        l1 = QVBoxLayout(w1)
        l1.addWidget(self.canvas_raw)
        w2 = QWidget()
        l2 = QVBoxLayout(w2)
        l2.addWidget(self.canvas_pre)
        self.tabs.addTab(w1, "Raw")
        self.tabs.addTab(w2, "Preprocessed (for detection)")
        layout.addWidget(self.tabs)

    def run_preview(self, image_path: Path, params: PipelineParams) -> None:
        raw = io.load_image(image_path)
        pre = preprocess.preprocess_for_spots(raw, sigma=params.preprocess_sigma)
        spots = detect_spots(pre, params.spot_params)
        radius = max(2.0, float(params.spot_params.diameter) / 2.0)

        self.canvas_raw.show_image_with_spots(raw, spots, radius=radius)
        self.canvas_pre.show_image_with_spots(pre, spots, radius=radius)

        msg = (
            f"File: {image_path.name}\n"
            f"Engine: {params.spot_params.engine}, diameter={params.spot_params.diameter}, "
            f"minmass={params.spot_params.minmass}, separation={params.spot_params.separation}\n"
            f"Preprocess sigma: {params.preprocess_sigma}\n"
            f"Detected spots: {len(spots)}; {_spot_mass_stats(spots)}\n"
        )
        if len(spots) == 0:
            msg += (
                "\nTip: 如果检不出点，常见原因是 minmass 过高或 preprocess sigma 过大。\n"
                "- 先把 Min mass 调到 0 或更小，再逐步增大过滤噪声\n"
                "- 把 Preprocess σ 调低（例如 0–1）\n"
                "- 确认 diameter 与点大小匹配（200 nm 常见 5–9 px，取决于像素尺寸）\n"
            )
        self.info.setText(msg)

