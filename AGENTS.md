## Cursor Cloud specific instructions

### Overview

SpotDetec is a Python 3.10 desktop application for fluorescent spot detection on TIRF microscopy images. It has a PyQt5 GUI (Chinese and English versions) and a CLI for batch processing. There are no automated tests, no linter config, and no web server — it is a standalone desktop tool.

### Environment

- **Python 3.10** is required (installed via `deadsnakes` PPA, not conda).
- A virtualenv at `.venv` is used instead of the conda environment described in `README.md`.
- Activate with: `source .venv/bin/activate`
- The xcb Qt platform plugin requires system libraries: `libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0`. These are pre-installed in the snapshot.

### Running the application

- **English GUI**: `DISPLAY=:1 python run_gui_en.py`
- **Chinese GUI**: `DISPLAY=:1 python run_gui.py`
- **CLI batch**: `python run_batch.py --mode single --input <file_or_dir> --output <output_dir>` (see `README.md` for full parameter list)

### Lint

No linter is configured in the repo. `flake8` is installed in the venv for basic checks:
```
flake8 --max-line-length=120 src/ gui/ gui_en/ run_batch.py run_gui.py run_gui_en.py
```
Pre-existing style issues (long lines, trailing blank lines) exist and are not regressions.

### Tests

No automated test suite exists. To validate changes, create a synthetic test TIFF image and run through CLI or GUI.

### Gotchas

- The GUI will crash if Qt xcb system libraries are missing. If you see `libxcb-icccm.so.4: cannot open shared object file`, install the libraries listed above.
- `DISPLAY=:1` must be set explicitly when launching the GUI (the env var may not be set in shells by default).
- PyQt5 is sensitive to the Python version; stick with Python 3.10.
