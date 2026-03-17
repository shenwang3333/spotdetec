"""English main window for Spots Detector and Correlator."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QSpinBox,
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont

from src.io import list_images, match_pairs_by_lower
from src.pipeline import PipelineParams, process_batch, process_single_file

from .params_en import SpotParamsWidgetEN, PipelineParamsWidgetEN
from .results_en import ResultsWidgetEN
from .preview_en import PreviewDialogEN


class WorkerEN(QThread):
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

                results = process_batch(self.batch_paths, self.output_dir, self.params, self.mode, progress_callback=cb)
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


class MainWindowEN(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Spots Detector and Correlator")
        self.setMinimumSize(860, 620)
        self.resize(980, 720)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Mode
        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_group)
        self.mode_single = QRadioButton("Single-channel: size/intensity/count/area fraction")
        self.mode_dual = QRadioButton("Dual-channel: correlation, ratios, and counts")
        self.mode_single.setChecked(True)
        mode_layout.addWidget(self.mode_single)
        mode_layout.addWidget(self.mode_dual)
        layout.addWidget(mode_group)

        # Input
        input_group = QGroupBox("Inputs")
        input_layout = QVBoxLayout(input_group)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Input (file/folder):"))
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Single image file or folder")
        row1.addWidget(self.input_edit)
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self._browse_input)
        row1.addWidget(self.browse_btn)
        input_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Upper (dual only):"))
        self.input_upper_edit = QLineEdit()
        self.input_upper_edit.setPlaceholderText("Upper image file or folder (for folder pairing)")
        row2.addWidget(self.input_upper_edit)
        self.browse_upper_btn = QPushButton("Browse…")
        self.browse_upper_btn.clicked.connect(self._browse_upper)
        row2.addWidget(self.browse_upper_btn)
        input_layout.addLayout(row2)

        dual_in_group = QGroupBox("Dual-channel input strategy (dual mode only)")
        dual_in_layout = QVBoxLayout(dual_in_group)
        self.dual_mode_channels = QRadioButton("Mode 1: One multi-channel TIFF (use channel indices; leave Upper empty)")
        self.dual_mode_folders = QRadioButton("Mode 2: Two folders (pair by same filename stem; missing upper is skipped)")
        self.dual_mode_channels.setChecked(True)
        dual_in_layout.addWidget(self.dual_mode_channels)
        dual_in_layout.addWidget(self.dual_mode_folders)
        input_layout.addWidget(dual_in_group)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Channel indices (Mode 1): lower, upper"))
        self.ch_lower = QSpinBox()
        self.ch_lower.setRange(0, 15)
        self.ch_lower.setValue(0)
        self.ch_upper = QSpinBox()
        self.ch_upper.setRange(0, 15)
        self.ch_upper.setValue(1)
        row3.addWidget(self.ch_lower)
        row3.addWidget(self.ch_upper)
        row3.addStretch()
        input_layout.addLayout(row3)

        layout.addWidget(input_group)

        # Output
        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Output folder:"))
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Where CSV/plots will be saved")
        out_row.addWidget(self.output_edit)
        self.browse_out_btn = QPushButton("Browse…")
        self.browse_out_btn.clicked.connect(self._browse_output)
        out_row.addWidget(self.browse_out_btn)
        layout.addLayout(out_row)

        # Params
        params_group = QGroupBox("Parameters")
        params_layout = QHBoxLayout(params_group)
        self.spot_params = SpotParamsWidgetEN()
        self.pipeline_params = PipelineParamsWidgetEN()
        params_layout.addWidget(self.spot_params)
        params_layout.addWidget(self.pipeline_params)
        layout.addWidget(params_group)

        # Run
        run_row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.setMinimumHeight(36)
        self.run_btn.clicked.connect(self._run)
        run_row.addWidget(self.run_btn)
        self.preview_btn = QPushButton("Preview (single image)")
        self.preview_btn.setMinimumHeight(36)
        self.preview_btn.clicked.connect(self._preview)
        run_row.addWidget(self.preview_btn)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        run_row.addWidget(self.progress_bar)
        layout.addLayout(run_row)

        # Log
        layout.addWidget(QLabel("Log:"))
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(120)
        self.log_edit.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_edit)

        # Results
        self.results_widget = ResultsWidgetEN()
        layout.addWidget(self.results_widget)

        self._worker: WorkerEN | None = None
        self.dual_mode_channels.toggled.connect(self._sync_dual_widgets)
        self.dual_mode_folders.toggled.connect(self._sync_dual_widgets)
        self.mode_single.toggled.connect(self._sync_dual_widgets)
        self.mode_dual.toggled.connect(self._sync_dual_widgets)
        self._sync_dual_widgets()

    def _log(self, msg: str) -> None:
        self.log_edit.append(msg)

    def _sync_dual_widgets(self) -> None:
        dual = self.mode_dual.isChecked()
        self.input_upper_edit.setEnabled(dual and self.dual_mode_folders.isChecked())
        self.browse_upper_btn.setEnabled(dual and self.dual_mode_folders.isChecked())
        self.ch_lower.setEnabled(dual and self.dual_mode_channels.isChecked())
        self.ch_upper.setEnabled(dual and self.dual_mode_channels.isChecked())

    def _browse_input(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select input folder")
        if dir_path:
            self.input_edit.setText(dir_path)
            return
        path, _ = QFileDialog.getOpenFileName(self, "Select image file", "", "Images (*.tif *.tiff *.png);;All (*.*)")
        if path:
            self.input_edit.setText(path)

    def _browse_upper(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select upper folder")
        if dir_path:
            self.input_upper_edit.setText(dir_path)
            return
        path, _ = QFileDialog.getOpenFileName(self, "Select upper image file", "", "Images (*.tif *.tiff *.png);;All (*.*)")
        if path:
            self.input_upper_edit.setText(path)

    def _browse_output(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select output folder")
        if dir_path:
            self.output_edit.setText(dir_path)

    def _run(self) -> None:
        inp = self.input_edit.text().strip()
        out = self.output_edit.text().strip()
        if not inp:
            QMessageBox.warning(self, "Input", "Please set an input file/folder.")
            return
        if not out:
            QMessageBox.warning(self, "Output", "Please set an output folder.")
            return

        input_path = Path(inp)
        output_dir = Path(out)
        if not input_path.exists():
            QMessageBox.critical(self, "Error", f"Input path does not exist: {input_path}")
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
                if not input_path.is_file():
                    QMessageBox.warning(self, "Dual Mode 1", "Mode 1 requires a single multi-channel TIFF file as input.")
                    return
                channels_from_one = (self.ch_lower.value(), self.ch_upper.value())
            else:
                upper_text = self.input_upper_edit.text().strip()
                if not upper_text:
                    QMessageBox.warning(self, "Dual Mode 2", "Mode 2 requires an upper folder.")
                    return
                path_upper = Path(upper_text)
                if input_path.is_dir() and path_upper.is_dir():
                    pairs, missing = match_pairs_by_lower(input_path, path_upper)
                    if missing:
                        self._log(f"Warning: {len(missing)} lower images have no matching upper; they will be skipped.")
                    batch_paths = [(p1, p2) for (p1, p2) in pairs]
                    path_upper = None
                elif input_path.is_file() and path_upper.is_file():
                    batch_paths = None
                else:
                    QMessageBox.warning(self, "Dual Mode 2", "Please provide either two folders or two files.")
                    return
        else:
            if input_path.is_file():
                batch_paths = None
            else:
                batch_paths = [(p, None) for p in list_images(input_path)]

        if batch_paths is not None and len(batch_paths) == 0:
            QMessageBox.warning(self, "Input", "No images found / no pairs matched.")
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100 if batch_paths else 1)
        self.progress_bar.setValue(0)
        self.log_edit.clear()

        if batch_paths:
            self._worker = WorkerEN(
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
            self._worker = WorkerEN(
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
        self._log("Batch completed.")

    def _on_single_finished(self, result) -> None:
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self._worker = None
        mode = "dual" if self.mode_dual.isChecked() else "single"
        self.results_widget.set_result(result, mode, Path(self.output_edit.text()))
        self._log("Done.")

    def _on_error(self, msg: str) -> None:
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self._worker = None
        QMessageBox.critical(self, "Error", msg)
        self._log(f"Error: {msg}")

    def _preview(self) -> None:
        inp = self.input_edit.text().strip()
        if not inp:
            QMessageBox.warning(self, "Preview", "Please select a single image file (or pick a folder then select a file).")
            return
        input_path = Path(inp)
        if input_path.is_dir():
            path, _ = QFileDialog.getOpenFileName(self, "Select an image for preview", str(input_path), "Images (*.tif *.tiff *.png);;All (*.*)")
            if not path:
                return
            input_path = Path(path)
        if not input_path.exists() or not input_path.is_file():
            QMessageBox.warning(self, "Preview", f"Invalid image path: {input_path}")
            return
        spot_params = self.spot_params.get_spot_params()
        params = self.pipeline_params.get_pipeline_params(spot_params)
        dlg = PreviewDialogEN(self)
        try:
            dlg.run_preview(input_path, params)
        except Exception as e:
            QMessageBox.critical(self, "Preview failed", str(e))
            return
        dlg.exec_()

