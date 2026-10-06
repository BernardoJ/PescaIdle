"""Exercise the frozen executable from a foreign cwd with an isolated save."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
out=root/'docs'/'visual'/'executavel'
with tempfile.TemporaryDirectory(prefix='pesca-exe-') as tmp:
    env=os.environ.copy()
    env['PESCA_IDLE_SAVE_PATH']=str(Path(tmp)/'save.json')
    env['PESCA_IDLE_SMOKE_DIR']=str(out)
    env['QT_QPA_PLATFORM']='windows'
    exe=Path(sys.argv[1]) if len(sys.argv)>1 else root/'dist'/'PescaIdle.exe'
    process=subprocess.run([str(exe),'--smoke-test'],
                           cwd=tmp,env=env,timeout=60,capture_output=True,text=True)
    if process.returncode:
        print(process.stdout)
        print(process.stderr)
    assert process.returncode==0,process.returncode
    report=json.loads((out/'resultado.json').read_text(encoding='utf-8'))
    assert report['frozen'] and report['assets'] and report['ui_icon'],report
    assert report['cosmetic_sprites']==45,report
    assert isinstance(report['physical_scale'],int),report
    assert report['scene']==[256,144] and Path(tmp,'save.json').exists(),report
    assert report['clock_source']=='device_local' and report['light_plates']==96,report
    assert report['animated_pets']==14 and report['animated_flags']==13,report
    assert 0<=report['clock_position']<1,report
    assert all((out/f'horario-{hour:02d}-executavel.png').exists() for hour in (0,6,9,12,18,22)),report
    print('Frozen EXE passed: assets, day/night clock, all animated pets/flags, UI and isolated save; foreign cwd.')
