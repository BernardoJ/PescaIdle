"""Run source or freshly built Windows EXE using three isolated processes."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--exe',type=Path);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();out=args.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out==ROOT/'qa':ap.error('Use pasta nova em qa.')
    out.mkdir(parents=True,exist_ok=False)
    for part in ['tmp','appdata','localappdata']:(out/part).mkdir()
    env=os.environ.copy();env.update(PESCA_IDLE_SAVE_PATH=str(out/'save.json'),PESCA_IDLE_CLIMATE_QA_DIR=str(out/'evidence'),
        APPDATA=str(out/'appdata'),LOCALAPPDATA=str(out/'localappdata'),TEMP=str(out/'tmp'),TMP=str(out/'tmp'),QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
    command=[str(args.exe.resolve())] if args.exe else [sys.executable,'-X','utf8','-B',str(ROOT/'piloto_entry.py')]
    rows=[]
    for mode in ['pending','deliver','reopen']:
        start=time.perf_counter()
        with (out/(mode+'.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run([*command,'--climate-smoke',mode],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        if result.returncode:raise RuntimeError('Falha no smoke '+mode+'; consulte o log sintético.')
        report=json.loads((out/'evidence'/(mode+'.json')).read_text(encoding='utf-8'))
        assert report['frozen']==bool(args.exe) and report['schema']==5
        rows.append(dict(mode=mode,exit_code=0,seconds=time.perf_counter()-start,frozen=report['frozen']))
        print(mode+': PASSOU',flush=True)
    (out/'summary.json').write_text(json.dumps(dict(steps=rows,success=True,profile_isolated=True),indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
