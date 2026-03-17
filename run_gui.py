"""GUI entry point for TIRF liposome analysis."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root so that "from src ..." and "from gui ..." work when run as script or from PyInstaller
if getattr(sys, "frozen", False):
    _root = Path(sys.executable).parent
else:
    _root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui.main_window import MainWindow


def main() -> None:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("TIRF 脂质体分析")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
