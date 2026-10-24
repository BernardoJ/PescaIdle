# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os
import json

demo_build = os.getenv('PESCA_IDLE_DEMO_BUILD') == '1'
demo_datas = []
demo_name = None
if demo_build:
    info_path = Path(os.environ['PESCA_IDLE_DEMO_BUILD_INFO'])
    info = json.loads(info_path.read_text(encoding='utf-8'))
    demo_name = 'PescaIdle-Tamanhos-Demo-' + info['source_commit'][:8]
    demo_datas = [(str(info_path), '.'),
                  (str(Path(SPECPATH) / 'tools/fixtures/demo_tamanhos.json'), 'tools/fixtures')]

a = Analysis(
    ['demo_entry.py' if demo_build else 'piloto_entry.py'],
    pathex=[],
    binaries=[],
    datas=[(str(p), str(Path('assets') / p.parent.relative_to(Path(SPECPATH) / 'assets')))
           for p in (Path(SPECPATH) / 'assets').rglob('*')
           if p.suffix in ('.png', '.json')
           and 'source' not in p.relative_to(Path(SPECPATH) / 'assets').parts] + demo_datas,
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
    name=demo_name if demo_build else 'PescaIdle-Clima' if os.getenv('PESCA_IDLE_CLIMATE_BUILD')=='1' else 'PescaIdle-Tamanhos-Piloto',
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
