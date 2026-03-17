"""Parameter widgets (English)."""

from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox

from src.spot_detection import SpotParams
from src.pipeline import PipelineParams


class SpotParamsWidgetEN(QWidget):
    """Controls for spot detection (diameter, minmass, separation, engine)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)

        self.diameter = QSpinBox()
        self.diameter.setRange(3, 99)
        self.diameter.setValue(7)
        self.diameter.setSingleStep(2)
        self.diameter.setToolTip(
            "<b>Diameter (px)</b><br>"
            "Characteristic spot size in pixels (prefer odd).<br><br>"
            "<b>What it means</b><br>"
            "- Roughly the width/diameter of a single diffraction-limited bright spot in your image.<br>"
            "- Too small: may over-split one spot / more noise detections.<br>"
            "- Too large: may merge nearby spots / smooth away weak spots.<br><br>"
            "<b>Start here</b><br>"
            "- Commonly try 5 / 7 / 9 for ~200 nm liposomes (depends on pixel size and optics)."
        )
        layout.addRow("Diameter (px):", self.diameter)

        self.minmass = QDoubleSpinBox()
        self.minmass.setRange(0, 1e12)
        self.minmass.setValue(0)
        self.minmass.setDecimals(2)
        self.minmass.setToolTip(
            "<b>Min mass</b><br>"
            "Minimum integrated brightness used to filter noisy detections.<br><br>"
            "<b>If you get 0 spots</b><br>"
            "- Most often Min mass is too high. Try setting it to 0 first, then increase slowly."
        )
        layout.addRow("Min mass:", self.minmass)

        self.separation = QDoubleSpinBox()
        self.separation.setRange(0, 100)
        self.separation.setValue(0)
        self.separation.setDecimals(1)
        self.separation.setSpecialValueText("Auto")
        self.separation.setToolTip(
            "<b>Separation (px)</b><br>"
            "Minimum distance allowed between two spot centers.<br><br>"
            "<b>0 = Auto</b><br>"
            "- Uses a value comparable to Diameter to avoid double-counting one spot."
        )
        layout.addRow("Separation (px):", self.separation)

        self.engine = QComboBox()
        self.engine.addItems(["trackpy", "LoG", "DoG"])
        self.engine.setToolTip(
            "<b>Engine</b><br>"
            "Spot detection backend.<br><br>"
            "<b>trackpy</b>: recommended default (Gaussian-like spots, outputs mass/size).<br>"
            "<b>LoG/DoG</b>: scikit-image blob detectors as alternatives."
        )
        layout.addRow("Engine:", self.engine)

        self.preprocess = QCheckBox("Preprocess inside engine")
        self.preprocess.setChecked(True)
        self.preprocess.setToolTip(
            "<b>Preprocess inside engine</b><br>"
            "Enable internal preprocessing (e.g. band-pass) used by the detector. Usually keep ON."
        )
        layout.addRow("", self.preprocess)

    def get_spot_params(self) -> SpotParams:
        sep_val = float(self.separation.value())
        sep = None if sep_val <= 0 else sep_val
        engine_map = {"trackpy": "trackpy", "LoG": "log", "DoG": "dog"}
        d = self.diameter.value()
        if d % 2 == 0:
            d += 1
        return SpotParams(
            diameter=d,
            minmass=self.minmass.value(),
            separation=sep,
            preprocess=self.preprocess.isChecked(),
            engine=engine_map[self.engine.currentText()],
        )


class PipelineParamsWidgetEN(QWidget):
    """Preprocess sigma, sub-mask radius (dual), pixel scale."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)

        self.preprocess_sigma = QDoubleSpinBox()
        self.preprocess_sigma.setRange(0, 10)
        self.preprocess_sigma.setValue(1.0)
        self.preprocess_sigma.setSingleStep(0.5)
        self.preprocess_sigma.setToolTip(
            "<b>Preprocess σ</b><br>"
            "Gaussian smoothing before detection. 0 = off.<br>"
            "Too large σ may remove weak spots (0 detections)."
        )
        layout.addRow("Preprocess σ:", self.preprocess_sigma)

        self.sub_mask_radius = QDoubleSpinBox()
        self.sub_mask_radius.setRange(1, 50)
        self.sub_mask_radius.setValue(5.0)
        self.sub_mask_radius.setDecimals(1)
        self.sub_mask_radius.setToolTip(
            "<b>Sub-mask radius (dual)</b><br>"
            "In dual-channel mode: radius around each LOWER spot to quantify UPPER intensity and count.<br>"
            "Too small: miss tethered upper spots; too large: include neighbors."
        )
        layout.addRow("Sub-mask radius (dual):", self.sub_mask_radius)

        self.pixel_scale = QDoubleSpinBox()
        self.pixel_scale.setRange(0.01, 100)
        self.pixel_scale.setValue(1.0)
        self.pixel_scale.setToolTip(
            "<b>Pixel scale</b><br>"
            "Optional unit scaling for area-related numbers. Keep 1.0 if unsure."
        )
        layout.addRow("Pixel scale:", self.pixel_scale)

    def get_pipeline_params(self, spot_params: SpotParams) -> PipelineParams:
        return PipelineParams(
            spot_params=spot_params,
            preprocess_sigma=self.preprocess_sigma.value(),
            sub_mask_radius_pixels=self.sub_mask_radius.value(),
            pixel_scale=self.pixel_scale.value(),
        )

