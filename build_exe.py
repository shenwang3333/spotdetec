"""Build Windows executable with PyInstaller. Run from project root: python build_exe.py"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Spots_Detector_and_Correlator",
        "--windowed",
        "--onefile",
        "--clean",
        f"--paths={ROOT}",
        "--hidden-import=trackpy",
        "--hidden-import=tifffile",
        "--hidden-import=pandas",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.backends.backend_qt5agg",
        "--hidden-import=scipy.ndimage",
        "--hidden-import=skimage",
        "--hidden-import=skimage.feature",
        "--hidden-import=skimage.filters",
        "--collect-all=trackpy",
        str(ROOT / "run_gui.py"),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    print("Build done. Executable: dist/Spots_Detector_and_Correlator_zh.exe")


if __name__ == "__main__":
    main()
