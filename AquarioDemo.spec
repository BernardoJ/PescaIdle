# Separate, memory-only visual demonstration; historical builds remain intact.
from pathlib import Path
import json
import os

info_path=Path(os.environ['PESCA_IDLE_AQUARIUM_BUILD_INFO'])
info=json.loads(info_path.read_text(encoding='utf-8'))
a=Analysis(['aquario_demo.py'],pathex=[],binaries=[],
    datas=[(str(p),str(Path('assets')/p.parent.relative_to(Path(SPECPATH)/'assets')))
           for p in (Path(SPECPATH)/'assets').rglob('*')
           if p.suffix in ('.png','.json') and 'source' not in p.relative_to(Path(SPECPATH)/'assets').parts]
          +[(str(info_path),'.')],
    hiddenimports=[],hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],
    noarchive=False,optimize=0)
a.binaries=[e for e in a.binaries
    if not Path(e[0]).name.lower().startswith(('api-ms-','ext-ms-'))
    and Path(e[0]).name.lower()!='ucrtbase.dll'
    and not (Path(e[0]).name.lower().startswith('icu') and Path(e[1]).parent.name.lower()!='pyside6')]
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],
    name='PescaIdle-Aquario-Demo-'+info['source_commit'][:8],
    debug=False,bootloader_ignore_signals=False,strip=False,upx=False,
    runtime_tmpdir=None,console=False,disable_windowed_traceback=False,
    target_arch=None,codesign_identity=None,entitlements_file=None)
