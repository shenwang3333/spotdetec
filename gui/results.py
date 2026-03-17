"""Results display: summary text, table preview, and export."""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from src.single_channel import SingleChannelResult
    from src.dual_channel import DualChannelResult


def _fmt(v) -> str:
    if v is None or (hasattr(v, "__float__") and math.isnan(float(v))):
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:.4f}" if isinstance(v, float) else str(v)
    return str(v)


def _summary_text_single(result: "SingleChannelResult") -> str:
    s = result.summary
    return (
        f"Total count: {s['count']}\n"
        f"Size — mean: {_fmt(s.get('size_mean'))}, median: {_fmt(s.get('size_median'))}, std: {_fmt(s.get('size_std'))}\n"
        f"Intensity — mean: {_fmt(s.get('intensity_mean'))}, median: {_fmt(s.get('intensity_median'))}\n"
        f"Area fraction: {s.get('area_fraction', 0):.6f}\n"
        f"Total spot area: {s.get('total_spot_area', 0):.2f} px²"
    )


def _summary_text_dual(result: "DualChannelResult") -> str:
    s = result.summary
    return (
        f"Lower count: {s['lower_count']}, Upper count: {s['upper_count']}\n"
        f"Upper intensity in mask (total): {s.get('upper_intensity_in_mask_total', 0):.2f}\n"
        f"Intensity ratio (upper/lower) — mean: {_fmt(s.get('intensity_ratio_mean'))}, "
        f"median: {_fmt(s.get('intensity_ratio_median'))}\n"
        f"Upper per lower count — mean: {_fmt(s.get('upper_per_lower_count_mean'))}, "
        f"median: {_fmt(s.get('upper_per_lower_count_median'))}"
    )


class ResultsWidget(QWidget):
    """Show last result summary and optional table; button to export."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.summary_edit = QTextEdit()
        self.summary_edit.setReadOnly(True)
        self.summary_edit.setPlaceholderText("Run analysis to see summary here.")
        layout.addWidget(self.summary_edit)
        self.tabs = QTabWidget()
        self.table = QTableWidget()
        self.tabs.addTab(self.table, "Table preview")
        layout.addWidget(self.tabs)
        self.export_btn = QPushButton("Export CSV / plots to folder...")
        self.export_btn.clicked.connect(self._on_export)
        layout.addWidget(self.export_btn)
        self._last_result = None
        self._last_mode = "single"
        self._last_output_dir: Path | None = None

    def set_result(
        self,
        result: "SingleChannelResult | DualChannelResult",
        mode: str,
        output_dir: Path | None = None,
    ) -> None:
        self._last_result = result
        self._last_mode = mode
        self._last_output_dir = output_dir
        if mode == "single":
            self.summary_edit.setText(_summary_text_single(result))
            self._fill_table_single(result)
        else:
            self.summary_edit.setText(_summary_text_dual(result))
            self._fill_table_dual(result)

    def _fill_table_single(self, result: "SingleChannelResult") -> None:
        self.table.clear()
        if len(result.spots) == 0:
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return
        cols = ["x", "y", "mass", "size", "area"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(len(result.spots))
        for r in range(len(result.spots)):
            self.table.setItem(r, 0, QTableWidgetItem(f"{result.spots['x'][r]:.2f}"))
            self.table.setItem(r, 1, QTableWidgetItem(f"{result.spots['y'][r]:.2f}"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{result.spots['mass'][r]:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{result.spots['size'][r]:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{result.area_per_spot[r]:.2f}"))
        self.table.resizeColumnsToContents()

    def _fill_table_dual(self, result: "DualChannelResult") -> None:
        self.table.clear()
        if len(result.lower_spots) == 0:
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return
        cols = ["lower_x", "lower_y", "lower_mass", "upper_int", "upper_count", "ratio"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setRowCount(len(result.lower_spots))
        for r in range(len(result.lower_spots)):
            self.table.setItem(r, 0, QTableWidgetItem(f"{result.lower_spots['x'][r]:.2f}"))
            self.table.setItem(r, 1, QTableWidgetItem(f"{result.lower_spots['y'][r]:.2f}"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{result.lower_spots['mass'][r]:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{result.per_lower_upper_intensity[r]:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(str(result.per_lower_upper_count[r])))
            self.table.setItem(r, 5, QTableWidgetItem(f"{result.per_lower_intensity_ratio[r]:.4f}"))
        self.table.resizeColumnsToContents()

    def _on_export(self) -> None:
        if self._last_output_dir is not None and self._last_output_dir.exists():
            QMessageBox.information(
                self,
                "Export",
                f"Results and plots were already saved to:\n{self._last_output_dir}",
            )
            return
        QMessageBox.information(
            self,
            "Export",
            "CSV and plots are written automatically to the chosen output folder when you run analysis.",
        )
