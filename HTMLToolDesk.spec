# -*- mode: python ; coding: utf-8 -*-
# Fast, one-directory build. Keep all generated files together.
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=['PyQt6.QtSvg', 'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6', 'PyQt5', 'PySide2'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='HTMLToolDesk',
    console=False,
    debug=False,
    strip=False,
    upx=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=False,
    name='HTMLToolDesk',
)
