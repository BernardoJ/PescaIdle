"""Phase 1 wrapper: existing snapshot tools, explicit disposable persistence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / 'snapshot-verificado'
PYTHON = ROOT.parent / 'PescaIdle-integracao-20261006/.venv/Scripts/python.exe'
OPTIONS = {
    'suite': ('validate_game.py', [], 'offscreen', '1'),
    'mobile': ('validate_mobile.py', [], 'offscreen', '1'),
    'native100': ('validate_museum.py', ['--native-visual'], 'windows', '1'),
    'native125': ('validate_museum.py', ['--native-visual'], 'windows', '1.25'),
    'measure': ('measure_museum_baseline.py', [], 'offscreen', '1'),
}
name = sys.argv[1]
run_label = sys.argv[2] if len(sys.argv) > 2 else name
script, args, backend, scale = OPTIONS[name]
out = ROOT / 'qa' / run_label
out.mkdir(parents=True, exist_ok=False)
temporary = ROOT / 'qa/temporarios' / run_label
temporary.mkdir(parents=True, exist_ok=False)
profile = ROOT / 'qa/perfis' / run_label
profile.mkdir(parents=True, exist_ok=False)
env = os.environ.copy()
for key in ('PESCA_IDLE_MOBILE', 'PESCA_IDLE_CONSOLE', 'PYTHONPATH', 'PYTHONOPTIMIZE'):
    env.pop(key, None)
env.update(
    PESCA_IDLE_SAVE_PATH=str(profile / 'guard.json'),
    APPDATA=str(profile / 'appdata'), LOCALAPPDATA=str(profile / 'localappdata'),
    PESCA_IDLE_QA_DIR=str(out), PESCA_IDLE_MEASURE_SOURCE=str(SNAPSHOT),
    TEMP=str(temporary), TMP=str(temporary),
    PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
    PYTHONIOENCODING='utf-8',
    QT_QPA_PLATFORM=backend, QT_SCALE_FACTOR=scale,
)
for key in ('PESCA_IDLE_SAVE_PATH', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP'):
    if not Path(env[key]).resolve().is_relative_to((ROOT / 'qa').resolve()):
        raise RuntimeError('Persistence isolation failed: ' + key)
command = [str(PYTHON), str(SNAPSHOT / 'tools' / script), *args]
started = time.time()
metadata = dict(name=name, run_label=run_label, log_encoding='utf-8', command=command, cwd=str(SNAPSHOT),
                explicit_environment={key: env[key] for key in (
                    'PESCA_IDLE_SAVE_PATH', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP',
                    'PESCA_IDLE_QA_DIR', 'PESCA_IDLE_MEASURE_SOURCE',
                    'QT_QPA_PLATFORM', 'QT_SCALE_FACTOR', 'PYTHONDONTWRITEBYTECODE')},
                started_utc=started, source_commit='2a0353ff7c1cae2dca69d08c222b0660770d4385')
(out / 'execucao.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
print('START', name, flush=True)
with (out / 'execucao.log').open('wb') as log:
    process = subprocess.run(command, cwd=SNAPSHOT, env=env, stdout=log, stderr=subprocess.STDOUT)
metadata.update(exit_code=process.returncode, elapsed_seconds=time.time()-started,
                finished_utc=time.time())
(out / 'execucao.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
print('END', name, 'exit', process.returncode, 'seconds', round(metadata['elapsed_seconds'], 2), flush=True)
print((out / 'execucao.log').read_text(encoding='utf-8', errors='replace')[-6000:], flush=True)
sys.exit(process.returncode)
