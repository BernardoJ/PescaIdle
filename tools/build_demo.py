"""Build a separate Windows demo with the existing PyInstaller toolchain only."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.demo_tamanhos import source_snapshot


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True, help='New directory inside dist/')
    args = ap.parse_args()
    if os.name != 'nt':
        raise ValueError('Este build exige Windows; nenhuma ferramenta será instalada.')
    versions = {name: importlib.metadata.version(name) for name in ('PyInstaller', 'PySide6')}
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--name-only', 'HEAD'], text=True).strip()
    untracked = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '--others', '--exclude-standard'], text=True).strip()
    # Build code must have an immutable commit; docs-only modifications may follow.
    if any(n.endswith(('.py', '.spec', '.json', '.png')) for n in (dirty+'\n'+untracked).splitlines()):
        raise ValueError('Commit o código/assets revisados antes de gerar a build identificada.')
    output = args.out.resolve()
    if not output.is_relative_to(ROOT / 'dist'):
        raise ValueError('Use uma saída nova em dist/ para preservar os executáveis anteriores.')
    output.mkdir(parents=True, exist_ok=False)
    work = ROOT / 'qa' / ('build-demo-' + head[:8])
    work.mkdir(parents=True, exist_ok=False)
    snapshot, files = source_snapshot()
    info = {'source_commit':head, 'source_snapshot':snapshot, 'files':files,
            'python':sys.version.split()[0], 'versions':versions, 'kind':'demo-tamanhos-v1'}
    # Name must match the runtime resource name; no mutable Git path inside the EXE.
    metadata = work / 'demo_build.json'
    metadata.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    env = dict(os.environ, PESCA_IDLE_DEMO_BUILD='1', PESCA_IDLE_DEMO_BUILD_INFO=str(metadata),
        PYINSTALLER_CONFIG_DIR=str(work / 'pyinstaller-cache'),
        PESCA_IDLE_SAVE_PATH=str(work / 'guard.json'), APPDATA=str(work / 'appdata'),
        LOCALAPPDATA=str(work / 'localappdata'), TEMP=str(work / 'tmp'), TMP=str(work / 'tmp'))
    for name in ('appdata', 'localappdata', 'tmp'):
        (work / name).mkdir()
    command = [sys.executable, '-B', '-m', 'PyInstaller', '--noconfirm', '--distpath', str(output),
               '--workpath', str(work / 'pyinstaller'), str(ROOT / 'PescaIdle.spec')]
    with (work / 'build.log').open('wb') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Build falhou; consulte o build.log na saída de QA.')
    exe = output / ('PescaIdle-Tamanhos-Demo-' + head[:8] + '.exe')
    if not exe.is_file():
        raise RuntimeError('Build terminou sem o executável esperado.')
    info.update(executable=exe.name, bytes=exe.stat().st_size,
                sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
    (output / 'BUILD.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in info.items() if k!='files'}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, importlib.metadata.PackageNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
