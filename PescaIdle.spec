# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

a = Analysis(
    ['pesca_idle.py'],
    pathex=[],
    binaries=[],
    datas=[(str(p), 'assets') for p in (Path(SPECPATH) / 'assets').iterdir()
           if p.suffix in ('.png', '.json')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Qt's Windows wheel uses OS UCRT/API sets and unversioned Windows ICU APIs.
# Poppler/libheif on PATH can contribute incompatible ICU and compatibility DLLs.
a.binaries = [entry for entry in a.binaries
              if not Path(entry[0]).name.lower().startswith(('api-ms-', 'ext-ms-'))
              and Path(entry[0]).name.lower() != 'ucrtbase.dll'
              and not (Path(entry[0]).name.lower().startswith('icu')
                       and Path(entry[1]).parent.name.lower() != 'pyside6')]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PescaIdleDebug' if os.getenv('PESCA_IDLE_CONSOLE') == '1' else 'PescaIdle',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=os.getenv('PESCA_IDLE_CONSOLE') == '1',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
