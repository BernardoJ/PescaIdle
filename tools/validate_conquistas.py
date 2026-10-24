"""Run approved achievement checks with synthetic profiles and bounded output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    out=args.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out==ROOT/'qa':
        ap.error('Use um diretório novo dentro de qa deste candidato.')
    out.mkdir(parents=True,exist_ok=False)
    for part in ('tmp','profiles','appdata','localappdata'):
        (out/part).mkdir()
    env=os.environ.copy()
    env.update(PESCA_IDLE_SAVE_PATH=str(out/'profiles'/'guard.json'),
               APPDATA=str(out/'appdata'),LOCALAPPDATA=str(out/'localappdata'),
               TEMP=str(out/'tmp'),TMP=str(out/'tmp'),QT_QPA_PLATFORM='offscreen',
               PESCA_IDLE_QA_DIR=str(out/'regressao'),PYTHONDONTWRITEBYTECODE='1')
    steps=[
        ('individuais',['tools/test_conquistas_etapa1.py','--out',str(out/'individual')]),
        ('tamanhos-pendentes',['-m','unittest','-v','tools.verificar_tamanhos','tools.test_save_pendente_piloto']),
        ('regressao',['tools/validate_game.py']),
    ]
    runs=[]
    for name,command in steps:
        started=time.perf_counter()
        try:
            with (out/(name+'.log')).open('w',encoding='utf-8') as log:
                completed=subprocess.run([sys.executable,'-X','utf8','-B',*command],
                                         cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                                         timeout=300,check=False)
            code=completed.returncode
        except subprocess.TimeoutExpired:
            code=2
        runs.append(dict(step=name,exit_code=code,seconds=round(time.perf_counter()-started,3),
                         command=['python','-X','utf8','-B',*[
                             str(Path(x).relative_to(ROOT)) if str(x).startswith(str(ROOT)) else x
                             for x in command]]))
        print(name+': '+('PASSOU' if code==0 else 'FALHOU'),flush=True)
        if code:
            break
    config=json.loads((ROOT/'assets/conquistas_etapa1.json').read_text(encoding='utf-8'))
    files=sorted([*ROOT.glob('pesca*.py'),*(ROOT/'assets').rglob('*.json')])
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report=dict(base=config['source_commit'],python=platform.python_version(),steps=runs,
                successful=len(runs)==len(steps) and all(x['exit_code']==0 for x in runs),
                source_sha256=hashes,
                limits='Qt offscreen; sem EXE, Android nativo ou sessão humana prolongada.',
                profiles='Somente fixtures sintéticas; ambiente definido antes de importar o jogo.')
    (out/'resumo.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if report['successful'] else 1


if __name__=='__main__':
    raise SystemExit(main())
