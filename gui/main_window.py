"""Main window: mode, paths, params, run, progress, results."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QSplitter,
    QMessageBox,
    QComboBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from src.io import list_images, match_pairs_by_lower
from src.pipeline import PipelineParams, process_batch, process_single_file
from .params import SpotParamsWidget, PipelineParamsWidget
from .results import ResultsWidget
from .preview import PreviewDialog


class Worker(QThread):
    """Run pipeline in background and emit progress/result."""
    progress = pyqtSignal(str)
    progress_batch = pyqtSignal(int, int, str)
    finished_single = pyqtSignal(object)
    finished_batch = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(
        self,
        mode: str,
        input_path: Path,
        output_dir: Path,
        params: PipelineParams,
        path_upper: Path | None = None,
        channels_from_one: tuple[int, int] | None = None,
        batch_paths: list[tuple[Path, Path | None]] | None = None,
    ) -> None:
        super().__init__()
        self.mode = mode
        self.input_path = input_path
        self.output_dir = output_dir
        self.params = params
        self.path_upper = path_upper
        self.channels_from_one = channels_from_one
        self.batch_paths = batch_paths

    def run(self) -> None:
        try:
            if self.batch_paths:
                def cb(i: int, n: int, msg: str) -> None:
                    self.progress_batch.emit(i, n, msg)
                results = process_batch(
                    self.batch_paths,
                    self.output_dir,
                    self.params,
                    self.mode,
                    progress_callback=cb,
                )
                self.finished_batch.emit(results)
            else:
                def cb(msg: str) -> None:
                    self.progress.emit(msg)
                result = process_single_file(
                    self.input_path,
                    self.output_dir,
                    self.params,
                    mode=self.mode,
                    path_upper=self.path_upper,
                    channels_from_one=self.channels_from_one,
                    progress_callback=cb,
                )
                self.finished_single.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TIRF 脂质体荧光分析")
        self.setMinimumSize(800, 600)
        self.resize(900, 650)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Mode
        mode_group = QGroupBox("分析模式")
        mode_layout = QVBoxLayout(mode_group)
        self.mode_single = QRadioButton("单通道：统计大小、强度、个数、面积占比")
        self.mode_dual = QRadioButton("双通道：下层/上层关联、强度比与计数分布")
        self.mode_single.setChecked(True)
        self.mode_single.setToolTip(
            "<b>单通道模式</b><br>"
            "只分析一个 channel：点检测后输出大小/强度分布、总个数、占视野面积比等。<br>"
            "适用于只想统计某个颜色的脂质体。"
        )
        self.mode_dual.setToolTip(
            "<b>双通道模式</b><br>"
            "下层作为 mask：在每个下层 spot 周围统计上层荧光总和、上层 spot 个数，并计算强度比（上/下）。<br>"
            "适用于 tether/correlation 分析。<br><br>"
            "<b>注意</b>：默认假设两通道已经对齐、同尺寸。"
        )
        mode_layout.addWidget(self.mode_single)
        mode_layout.addWidget(self.mode_dual)
        layout.addWidget(mode_group)

        # Input
        input_group = QGroupBox("输入")
        input_layout = QVBoxLayout(input_group)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("输入路径:"))
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("单张图像或文件夹路径")
        self.input_edit.setToolTip(
            "<b>输入路径</b><br>"
            "- 单通道：选择一张图或一个文件夹（批量）。<br>"
            "- 双通道：下层图像（文件）或下层文件夹（批量）。<br><br>"
            "支持 TIFF/PNG（推荐 TIFF）。"
        )
        row1.addWidget(self.input_edit)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setToolTip("选择输入文件夹（批量）或选择单张图片。")
        self.browse_btn.clicked.connect(self._browse_input)
        row1.addWidget(self.browse_btn)
        input_layout.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("上层路径 (双通道):"))
        self.input_upper_edit = QLineEdit()
        self.input_upper_edit.setPlaceholderText("双通道时：上层图像或文件夹（与下层按文件名配对）")
        self.input_upper_edit.setToolTip(
            "<b>上层路径（双通道）</b><br>"
            "双通道分析时使用：<br>"
            "- 如果你选择的是两个文件：这里选上层文件；输入路径选下层文件。<br>"
            "- 如果你选择的是两个文件夹：这里选上层文件夹；会按<b>同名文件</b>配对。<br><br>"
            "如果留空：表示你要用“单文件多通道”的方式（用下方通道索引）。"
        )
        row2.addWidget(self.input_upper_edit)
        self.browse_upper_btn = QPushButton("浏览...")
        self.browse_upper_btn.setToolTip("选择双通道时的上层文件或上层文件夹。")
        self.browse_upper_btn.clicked.connect(self._browse_upper)
        row2.addWidget(self.browse_upper_btn)
        input_layout.addLayout(row2)

        # Dual-channel input mode selector
        dual_in_group = QGroupBox("双通道输入方式（仅双通道模式下生效）")
        dual_in_layout = QVBoxLayout(dual_in_group)
        self.dual_mode_channels = QRadioButton("模式 1：单个 TIFF 含上下通道（用通道索引区分；上层路径留空）")
        self.dual_mode_folders = QRadioButton("模式 2：上下层分别在两个文件夹（同名配对；找不到上层则跳过并记录）")
        self.dual_mode_channels.setChecked(True)
        self.dual_mode_channels.setToolTip(
            "<b>模式 1：单文件多通道</b><br>"
            "输入路径选择单个 TIFF 文件，上层路径留空；用下方通道索引指定下层/上层。"
        )
        self.dual_mode_folders.setToolTip(
            "<b>模式 2：双文件夹配对</b><br>"
            "输入路径选择下层文件夹，上层路径选择上层文件夹；按<b>文件名(不含扩展名)</b>配对。<br>"
            "若某个下层找不到同名上层：会在日志里记录并跳过，继续下一张。"
        )
        dual_in_layout.addWidget(self.dual_mode_channels)
        dual_in_layout.addWidget(self.dual_mode_folders)
        input_layout.addWidget(dual_in_group)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("单文件双通道时通道索引:"))
        self.ch_lower = QSpinBox()
        self.ch_lower.setRange(0, 15)
        self.ch_lower.setValue(0)
        self.ch_upper = QSpinBox()
        self.ch_upper.setRange(0, 15)
        self.ch_upper.setValue(1)
        self.ch_lower.setToolTip(
            "<b>单文件多通道：下层通道索引</b><br>"
            "当上下层在同一个 TIFF 文件的不同通道里时使用。<br>"
            "例如下层在通道 0，上层在通道 1。"
        )
        self.ch_upper.setToolTip(
            "<b>单文件多通道：上层通道索引</b><br>"
            "当上下层在同一个 TIFF 文件的不同通道里时使用。"
        )
        row3.addWidget(self.ch_lower)
        row3.addWidget(QLabel("下层, 上层:"))
        row3.addWidget(self.ch_upper)
        row3.addStretch()
        input_layout.addLayout(row3)
        layout.addWidget(input_group)

        # Output
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("输出文件夹:"))
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("CSV 与分布图保存目录")
        self.output_edit.setToolTip(
            "<b>输出文件夹</b><br>"
            "会自动保存：<br>"
            "- 每张图的 spots CSV、summary CSV、分布图 PNG<br>"
            "- 批量处理时额外保存：batch_summary_single.csv / batch_summary_dual.csv"
        )
        out_row.addWidget(self.output_edit)
        self.browse_out_btn = QPushButton("浏览...")
        self.browse_out_btn.setToolTip("选择输出目录（会自动创建）。")
        self.browse_out_btn.clicked.connect(self._browse_output)
        out_row.addWidget(self.browse_out_btn)
        layout.addLayout(out_row)

        # Params
        params_group = QGroupBox("检测参数")
        params_layout = QHBoxLayout(params_group)
        self.spot_params = SpotParamsWidget()
        self.pipeline_params = PipelineParamsWidget()
        params_layout.addWidget(self.spot_params)
        params_layout.addWidget(self.pipeline_params)
        layout.addWidget(params_group)

        # Run
        run_row = QHBoxLayout()
        self.run_btn = QPushButton("运行分析")
        self.run_btn.setMinimumHeight(36)
        self.run_btn.setToolTip(
            "<b>运行分析</b><br>"
            "对当前输入（单张或文件夹批量）执行分析，并把结果写入输出文件夹。<br><br>"
            "新手建议：先用“预览/测试参数(单张)”把参数调到能检出点，再批量运行。"
        )
        self.run_btn.clicked.connect(self._run)
        run_row.addWidget(self.run_btn)
        self.preview_btn = QPushButton("预览/测试参数 (单张)")
        self.preview_btn.setMinimumHeight(36)
        self.preview_btn.setToolTip(
            "<b>预览/测试参数（单张）</b><br>"
            "用当前参数对一张图片运行点检测，并可视化圈出 spots。<br>"
            "适用于排查“批量时 0 spots / 参数不合适”。"
        )
        self.preview_btn.clicked.connect(self._preview)
        run_row.addWidget(self.preview_btn)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        run_row.addWidget(self.progress_bar)
        layout.addLayout(run_row)

        # Log
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(120)
        self.log_edit.setFont(QFont("Consolas", 9))
        layout.addWidget(QLabel("日志:"))
        layout.addWidget(self.log_edit)

        # Results
        self.results_widget = ResultsWidget()
        layout.addWidget(self.results_widget)

        self._worker: Worker | None = None
        self.dual_mode_channels.toggled.connect(self._sync_dual_input_widgets)
        self.dual_mode_folders.toggled.connect(self._sync_dual_input_widgets)
        self.mode_single.toggled.connect(self._sync_dual_input_widgets)
        self.mode_dual.toggled.connect(self._sync_dual_input_widgets)
        self._sync_dual_input_widgets()

    def _log(self, msg: str) -> None:
        self.log_edit.append(msg)

    def _sync_dual_input_widgets(self) -> None:
        """Enable/disable widgets based on selected mode and dual-input strategy."""
        dual = self.mode_dual.isChecked()
        # When not in dual mode, keep everything enabled but de-emphasize dual-only controls
        self.input_upper_edit.setEnabled(dual and self.dual_mode_folders.isChecked())
        self.browse_upper_btn.setEnabled(dual and self.dual_mode_folders.isChecked())
        self.ch_lower.setEnabled(dual and self.dual_mode_channels.isChecked())
        self.ch_upper.setEnabled(dual and self.dual_mode_channels.isChecked())

    def _browse_input(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if dir_path:
            self.input_edit.setText(dir_path)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择图像", "", "Images (*.tif *.tiff *.png);;All (*.*)"
            )
            if path:
                self.input_edit.setText(path)

    def _browse_upper(self) -> None:
        # Folder-first (more common for batch pairing), then fall back to single-file.
        dir_path = QFileDialog.getExistingDirectory(self, "选择上层图像文件夹")
        if dir_path:
            self.input_upper_edit.setText(dir_path)
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "选择上层图像（单文件）", "", "Images (*.tif *.tiff *.png);;All (*.*)"
        )
        if path:
            self.input_upper_edit.setText(path)

    def _browse_output(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if dir_path:
            self.output_edit.setText(dir_path)

    def _run(self) -> None:
        inp = self.input_edit.text().strip()
        out = self.output_edit.text().strip()
        if not inp:
            QMessageBox.warning(self, "输入", "请指定输入路径（文件或文件夹）。")
            return
        if not out:
            QMessageBox.warning(self, "输出", "请指定输出文件夹。")
            return
        input_path = Path(inp)
        output_dir = Path(out)
        if not input_path.exists():
            QMessageBox.critical(self, "错误", f"输入路径不存在: {input_path}")
            return
        output_dir.mkdir(parents=True, exist_ok=True)

        mode = "dual" if self.mode_dual.isChecked() else "single"
        spot_params = self.spot_params.get_spot_params()
        params = self.pipeline_params.get_pipeline_params(spot_params)

        batch_paths: list[tuple[Path, Path | None]] | None = None
        path_upper: Path | None = None
        channels_from_one: tuple[int, int] | None = None

        if mode == "dual":
            if self.dual_mode_channels.isChecked():
                # Mode 1: single file with channels
                if not input_path.is_file():
                    QMessageBox.warning(self, "双通道-模式1", "模式1 需要输入路径为单个 TIFF 文件。")
                    return
                channels_from_one = (self.ch_lower.value(), self.ch_upper.value())
                path_upper = None
                batch_paths = None
            else:
                # Mode 2: two folders (or two files)
                upper_text = self.input_upper_edit.text().strip()
                if not upper_text:
                    QMessageBox.warning(self, "双通道-模式2", "模式2 需要在“上层路径”选择上层文件夹。")
                    return
                path_upper = Path(upper_text)
                if input_path.is_dir() and path_upper.is_dir():
                    pairs, missing = match_pairs_by_lower(input_path, path_upper)
                    if missing:
                        self._log(f"Warning: {len(missing)} lower images have no matching upper; they will be skipped.")
                        for m in missing[:10]:
                            self._log(f"  missing upper for: {m.name}")
                        if len(missing) > 10:
                            self._log("  ... more missing not shown")
                    batch_paths = [(p1, p2) for (p1, p2) in pairs]
                    path_upper = None
                elif input_path.is_file() and path_upper.is_file():
                    batch_paths = None
                else:
                    QMessageBox.warning(self, "双通道-模式2", "模式2 请同时选择两个文件夹，或两个文件。")
                    return
        else:
            if input_path.is_file():
                batch_paths = None
            else:
                batch_paths = [(p, None) for p in list_images(input_path)]

        if batch_paths is not None and len(batch_paths) == 0:
            QMessageBox.warning(self, "输入", "未找到可配对的图像。")
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100 if batch_paths else 1)
        self.progress_bar.setValue(0)
        self.log_edit.clear()

        if batch_paths:
            self._worker = Worker(
                mode=mode,
                input_path=input_path,
                output_dir=output_dir,
                params=params,
                path_upper=path_upper,
                channels_from_one=channels_from_one,
                batch_paths=batch_paths,
            )
            self._worker.progress_batch.connect(self._on_batch_progress)
            self._worker.finished_batch.connect(self._on_batch_finished)
        else:
            self._worker = Worker(
                mode=mode,
                input_path=input_path,
                output_dir=output_dir,
                params=params,
                path_upper=path_upper,
                channels_from_one=channels_from_one,
            )
            self._worker.progress.connect(self._log)
            self._worker.finished_single.connect(self._on_single_finished)

        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _preview(self) -> None:
        inp = self.input_edit.text().strip()
        if not inp:
            QMessageBox.warning(self, "预览", "请先在“输入路径”选择一张图片（或先选文件夹再选单张）。")
            return
        input_path = Path(inp)
        if input_path.is_dir():
            path, _ = QFileDialog.getOpenFileName(
                self, "从该文件夹选择一张图片用于预览", str(input_path), "Images (*.tif *.tiff *.png);;All (*.*)"
            )
            if not path:
                return
            input_path = Path(path)
        if not input_path.exists() or not input_path.is_file():
            QMessageBox.warning(self, "预览", f"无效的图片路径: {input_path}")
            return
        spot_params = self.spot_params.get_spot_params()
        params = self.pipeline_params.get_pipeline_params(spot_params)
        dlg = PreviewDialog(self)
        try:
            dlg.run_preview(input_path, params)
        except Exception as e:
            QMessageBox.critical(self, "预览失败", str(e))
            return
        dlg.exec_()

    def _on_batch_progress(self, i: int, n: int, msg: str) -> None:
        self._log(msg)
        self.progress_bar.setMaximum(n)
        self.progress_bar.setValue(i + 1)

    def _on_batch_finished(self, results: list) -> None:
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self._worker = None
        if results:
            self.results_widget.set_result(results[-1], "dual" if self.mode_dual.isChecked() else "single", Path(self.output_edit.text()))
        self._log("批量处理完成。")

    def _on_single_finished(self, result) -> None:
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self._worker = None
        mode = "dual" if self.mode_dual.isChecked() else "single"
        self.results_widget.set_result(result, mode, Path(self.output_edit.text()))
        self._log("完成。")

    def _on_error(self, msg: str) -> None:
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self._worker = None
        QMessageBox.critical(self, "错误", msg)
        self._log(f"错误: {msg}")
