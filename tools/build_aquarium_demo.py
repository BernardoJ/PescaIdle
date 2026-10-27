"""Separate Windows visual-demo build, using the already installed toolchain."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if os.name!='nt':raise ValueError('Windows é necessário; nada será instalado.')
    versions={name:importlib.metadata.version(name) for name in ('PyInstaller','PySide6','Pillow')}
    head=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    changed=subprocess.check_output(['git','-C',str(ROOT),'diff','HEAD','--name-only'],text=True)
    changed+='\n'+subprocess.check_output(['git','-C',str(ROOT),'ls-files','--others','--exclude-standard'],text=True)
    if any(n.endswith(('.py','.spec','.json','.png')) for n in changed.splitlines()):
        raise ValueError('Registre primeiro o código/assets revisados; a build deve corresponder a um commit.')
    output=args.out.resolve()
    if not output.is_relative_to(ROOT/'dist') or output.exists():raise ValueError('Use uma pasta NOVA dentro de dist/.')
    output.mkdir(parents=True)
    work=ROOT/'qa'/('build-aquario-'+head[:8]);work.mkdir(parents=True,exist_ok=False)
    files=[*ROOT.glob('*.py'),ROOT/'AquarioDemo.spec',ROOT/'tools/aquarium_preview.py',
           ROOT/'tools/validate_aquarium_motion.py',ROOT/'tools/build_aquarium_demo.py']
    files += [p for p in (ROOT/'assets').rglob('*') if p.suffix in ('.png','.json') and 'source' not in p.parts]
    info=dict(source_commit=head,python=sys.version.split()[0],versions=versions,
        kind='aquarium-visual-memory-only',files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)})
    metadata=work/'aquario_build.json';metadata.write_text(json.dumps(info,indent=2),encoding='utf-8')
    env=dict(os.environ,PESCA_IDLE_AQUARIUM_BUILD_INFO=str(metadata),PYINSTALLER_CONFIG_DIR=str(work/'cache'),
        PESCA_IDLE_SAVE_PATH=str(work/'synthetic-never-written.json'),APPDATA=str(work/'appdata'),
        LOCALAPPDATA=str(work/'localappdata'),TEMP=str(work/'tmp'),TMP=str(work/'tmp'))
    for name in ('appdata','localappdata','tmp'):(work/name).mkdir()
    with (work/'build.log').open('wb') as log:
        result=subprocess.run([sys.executable,'-B','-m','PyInstaller','--noconfirm',
            '--distpath',str(output),'--workpath',str(work/'pyinstaller'),str(ROOT/'AquarioDemo.spec')],
            cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('Build falhou; veja qa/build-aquario-*/build.log.')
    exe=output/('PescaIdle-Aquario-Demo-'+head[:8]+'.exe')
    info.update(executable=exe.name,bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
    (output/'BUILD.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in info.items() if k!='files'}))


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,importlib.metadata.PackageNotFoundError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(2)
