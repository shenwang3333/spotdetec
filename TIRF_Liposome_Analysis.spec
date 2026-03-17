# PyInstaller spec for Spots Detector and Correlator GUI (zh)
# Run from project root: pyinstaller Spots Detector and Correlator.spec

block_cipher = None

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'trackpy', 'tifffile', 'pandas', 'numpy', 'scipy', 'scipy.ndimage',
        'matplotlib', 'matplotlib.backends.backend_qt5agg',
        'skimage', 'skimage.feature', 'skimage.filters', 'imageio',
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'src', 'src.io', 'src.preprocess', 'src.spot_detection',
        'src.single_channel', 'src.dual_channel', 'src.export', 'src.pipeline',
        'gui', 'gui.main_window', 'gui.params', 'gui.results',
        'gui.preview',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Spots_Detector_and_Correlator_zh',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
