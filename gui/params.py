"""Parameter widgets for spot detection and pipeline."""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QGroupBox,
    QVBoxLayout,
    QCheckBox,
    QLineEdit,
)
from PyQt5.QtCore import Qt

from src.spot_detection import SpotParams
from src.pipeline import PipelineParams


class SpotParamsWidget(QWidget):
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
            "用于点检测的“斑点特征尺寸”（像素，建议奇数）。<br><br>"
            "<b>怎么理解</b><br>"
            "- 近似等于单个spot在图像上的点扩散/亮斑直径（不是物理直径 200 nm 直接换算）。<br>"
            "- 该值太小：一个点可能被识别成多个/更容易受噪声影响。<br>"
            "- 该值太大：相邻点可能被合并，弱点更容易被抹平。<br><br>"
            "<b>建议起始值</b><br>"
            "- 常见从 5 / 7 / 9 试起（取决于像素尺寸与成像条件）。<br>"
            "- 用“预览/测试参数(单张)”看圈点是否贴合亮斑。"
        )
        layout.addRow("Diameter (px):", self.diameter)
        self.minmass = QDoubleSpinBox()
        self.minmass.setRange(0, 1e12)
        self.minmass.setValue(0)
        self.minmass.setDecimals(2)
        self.minmass.setToolTip(
            "<b>Min mass</b><br>"
            "最小“积分亮度”阈值（用于过滤噪声点）。<br><br>"
            "<b>怎么理解</b><br>"
            "- mass 越大，说明该点局部区域的总荧光越强。<br>"
            "- <b>如果你发现批量时 0 spots</b>：最常见原因就是 Min mass 设太高。<br><br>"
            "<b>调参建议</b><br>"
            "- 第一次建议先设为 0（确保不会错过弱点），确认能检出点后再逐步增加过滤噪声。<br>"
            "- 如果画面整体很暗、点强度差异很大：Min mass 往往需要更低。"
        )
        layout.addRow("Min mass:", self.minmass)
        self.separation = QDoubleSpinBox()
        self.separation.setRange(0, 100)
        self.separation.setValue(0)
        self.separation.setDecimals(1)
        self.separation.setSpecialValueText("Auto")
        self.separation.setToolTip(
            "<b>Separation (px)</b><br>"
            "两个 spots 之间允许的最小中心距离（像素）。<br><br>"
            "<b>0 = Auto</b><br>"
            "- 自动时通常会使用与 Diameter 同量级的距离，避免一个亮斑被重复计数。<br><br>"
            "<b>调大/调小会怎样</b><br>"
            "- 太小：同一个亮斑可能被识别成多个点（过分拆分）。<br>"
            "- 太大：相邻真实点可能被合并（漏检）。"
        )
        layout.addRow("Separation (px):", self.separation)
        self.engine = QComboBox()
        self.engine.addItems(["trackpy", "LoG", "DoG"])
        self.engine.setToolTip(
            "<b>Engine</b><br>"
            "选择点检测算法。<br><br>"
            "<b>trackpy</b><br>"
            "- 默认推荐：适合衍射极限点/近似高斯亮斑；输出包含 mass/size 等特征，便于统计。<br>"
            "<b>LoG/DoG</b><br>"
            "- scikit-image 的 blob 检测备选；当 trackpy 在某些图上不稳定时可尝试。"
        )
        layout.addRow("Engine:", self.engine)
        self.preprocess = QCheckBox("Preprocess in engine")
        self.preprocess.setChecked(True)
        self.preprocess.setToolTip(
            "<b>Preprocess in engine</b><br>"
            "是否启用检测算法内部的预处理（如 band-pass）。<br>"
            "一般保持开启；若你发现点被过度平滑或想完全手动控制预处理，可尝试关闭并只用 Preprocess σ。"
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


class PipelineParamsWidget(QWidget):
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
            "检测前的高斯平滑强度（sigma，像素）。<br><br>"
            "<b>0 = 关闭</b><br>"
            "- σ 越大：噪声越少，但弱小 spots 也可能被抹平（导致 0 spots）。<br>"
            "- σ 越小：保留更多细节，但可能出现更多噪声假阳性。<br><br>"
            "<b>建议</b><br>"
            "- 低信噪/很暗的图：优先用 0–1 试起。<br>"
            "- 如果 0 spots：先把 σ 调低，再看 Min mass。"
        )
        layout.addRow("Preprocess σ:", self.preprocess_sigma)
        self.sub_mask_radius = QDoubleSpinBox()
        self.sub_mask_radius.setRange(1, 50)
        self.sub_mask_radius.setValue(5.0)
        self.sub_mask_radius.setDecimals(1)
        self.sub_mask_radius.setToolTip(
            "<b>Sub-mask radius (dual)</b><br>"
            "双通道模式下：以每个“下层spot”为圆心，画一个圆形子区域（像素半径）。<br>"
            "在该圆内统计：上层荧光总和、上层 spot 个数，并计算强度比（上/下）。<br><br>"
            "<b>调参建议</b><br>"
            "- 通常设置为 Diameter/2 到 Diameter 之间（约 3–8 px 常见）。<br>"
            "- 太小：容易漏掉真实 tether（上层点在圆外）。<br>"
            "- 太大：会把邻近下层的上层信号算进来（污染比值）。"
        )
        layout.addRow("Sub-mask radius (dual):", self.sub_mask_radius)
        self.pixel_scale = QDoubleSpinBox()
        self.pixel_scale.setRange(0.01, 100)
        self.pixel_scale.setValue(1.0)
        self.pixel_scale.setToolTip(
            "<b>Pixel scale</b><br>"
            "用于把面积等量从“像素单位”换算到“物理单位”的比例因子。<br><br>"
            "<b>默认 1.0</b><br>"
            "- 目前主要影响“占视野面积比/总面积”等计算的单位缩放。<br>"
            "- 如果你暂时只关心相对比较，可保持 1.0。"
        )
        layout.addRow("Pixel scale:", self.pixel_scale)

    def get_pipeline_params(self, spot_params: SpotParams) -> PipelineParams:
        return PipelineParams(
            spot_params=spot_params,
            preprocess_sigma=self.preprocess_sigma.value(),
            sub_mask_radius_pixels=self.sub_mask_radius.value(),
            pixel_scale=self.pixel_scale.value(),
        )
