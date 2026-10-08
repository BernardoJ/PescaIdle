"""Current contracts; exact legacy suite/source preserved under docs/design."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='pesca-suite-') as tmp:
    out=Path(os.environ.get('PESCA_IDLE_QA_DIR',tmp))
    for name in ('validate_audit','validate_expansion','validate_cosmetics','balance_expansion'):
        env=os.environ.copy();env['PESCA_IDLE_SAVE_PATH']=str(Path(tmp)/(name+'.json'))
        env['APPDATA']=str(Path(tmp)/'appdata');env['LOCALAPPDATA']=str(Path(tmp)/'localappdata')
        env['PESCA_IDLE_QA_DIR']=str(out/name)
        subprocess.run([sys.executable,str(ROOT/'tools'/(name+'.py'))],cwd=ROOT,env=env,check=True)
    print('Expansion, preserved cosmetic checks and seeded balance passed.')
