"""Clean native Windows build from one exact, unmodified main checkout.

This tooling may live on a review branch. It does not patch the source checkout,
change its spec, reuse the repository's historical EXEs, or publish a release.
Deliverables are populated only after archive checks and native smoke pass.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.metadata
import json
import marshal
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import types

PINNED = {'PyInstaller':'6.22.3','PySide6':'6.11.2','Pillow':'12.3.0'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git(source, *args):
    return subprocess.check_output(['git','-C',str(source),*args],text=True).strip()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def canonical(code):
    consts=tuple(canonical(x) if isinstance(x,types.CodeType) else x for x in code.co_consts)
    return code.replace(co_filename='<source>',co_consts=consts)


def verify_archive(source, exe):
    from PyInstaller.archive.readers import CArchiveReader
    archive=CArchiveReader(str(exe))
    pyz=archive.open_embedded_archive('PYZ.pyz')
    records={}
    for name in sorted(pyz.toc):
        if not (name.startswith('pesca_') or name=='tools' or name.startswith('tools.')):
            continue
        path=source/(name.replace('.','/')+'.py')
        if not path.exists():
            path=source/name.replace('.','/')/'__init__.py'
        require(path.is_file(),'Bundled project module has no source: '+name)
        expected=canonical(compile(path.read_bytes(),str(path),'exec',dont_inherit=True,optimize=0))
        actual=canonical(pyz.extract(name))
        # Code equality compares the recursive code objects rather than marshal
        # intern/reference flags, which are not part of executable semantics.
        require(actual==expected,'Bundled bytecode differs from main: '+name)
        records[name]={'source_sha256':digest(path),'bytecode_equal':True}
    required={'pesca_save','pesca_idle','pesca_clima','pesca_piloto','pesca_pescaria',
              'pesca_offline','pesca_catalogo','pesca_tamanhos'}
    require(required<=records.keys(),'Required game modules are absent from EXE')
    entry=canonical(marshal.loads(archive.extract('piloto_entry')))
    expected=canonical(compile((source/'piloto_entry.py').read_bytes(),str(source/'piloto_entry.py'),
                               'exec',dont_inherit=True,optimize=0))
    require(entry==expected,'Bundled entrypoint differs from main')
    assets={}
    for path in sorted((source/'assets').rglob('*')):
        relative=path.relative_to(source)
        if not path.is_file() or path.suffix not in ('.png','.json') or 'source' in path.relative_to(source/'assets').parts:
            continue
        key=relative.as_posix()
        candidates=(key,key.replace('/','\\'))
        found=next((name for name in candidates if name in archive.toc),None)
        require(found is not None,'Missing packaged asset: '+key)
        require(hashlib.sha256(archive.extract(found)).hexdigest()==digest(path),'Packaged asset differs: '+key)
        assets[key]=digest(path)
    require(assets,'No production assets were verified')
    return dict(modules=records,entrypoint_equal=True,assets_sha256=assets,
                module_count=len(records),asset_count=len(assets),success=True)


def build(source, expected_commit, out):
    require(os.name=='nt' and platform.machine().lower() in ('amd64','x86_64'),
            'Build requires native Windows x64; cross-building on Linux is not supported.')
    source=source.resolve(strict=True);out=out.resolve()
    require(not out.exists(),'Use a NEW output directory; previous builds are never reused or overwritten.')
    require(not out.is_relative_to(source),'Build output must be outside the source checkout.')
    require(git(source,'rev-parse','HEAD')==expected_commit,'Source is not the approved main SHA')
    require(not git(source,'status','--porcelain=v2','--untracked-files=all'),'Source checkout is not clean')
    versions={name:importlib.metadata.version(name) for name in PINNED}
    require(versions==PINNED,'Build dependency versions differ from requirements-build.txt: '+str(versions))
    out.mkdir(parents=True)
    for name in ('tmp','appdata','localappdata','cache','package','qa'):(out/name).mkdir()
    source_guard=source/'qa'/('windows-clean-build-'+str(os.getpid()))
    source_guard.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy()
    for key in ('PESCA_IDLE_DEMO_BUILD','PESCA_IDLE_DEMO_BUILD_INFO','PESCA_IDLE_MOBILE',
                'PESCA_IDLE_CONSOLE','PESCA_IDLE_SAVE_PATH','PYTHONPATH','PYTHONHOME'):
        env.pop(key,None)
    env.update(PESCA_IDLE_CLIMATE_BUILD='1',PYINSTALLER_CONFIG_DIR=str(out/'cache'),
               TEMP=str(out/'tmp'),TMP=str(out/'tmp'),APPDATA=str(out/'appdata'),
               LOCALAPPDATA=str(out/'localappdata'),PESCA_IDLE_SAVE_PATH=str(source_guard/'guard.json'),
               PYTHONDONTWRITEBYTECODE='1')
    command=[sys.executable,'-X','utf8','-B','-m','PyInstaller','--clean','--noconfirm',
             '--distpath',str(out/'package'),'--workpath',str(out/'build'),str(source/'PescaIdle.spec')]
    with (out/'qa/build.log').open('wb') as log:
        result=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    require(result.returncode==0,'PyInstaller failed; inspect qa/build.log')
    built=out/'package/PescaIdle-Clima.exe'
    require(built.is_file(),'PyInstaller did not produce the expected new EXE')
    exe=out/'package'/('PescaIdle-Windows-'+expected_commit[:7]+'.exe')
    built.rename(exe)
    require(exe.read_bytes()[:2]==b'MZ','Output is not a Windows executable')
    archive=verify_archive(source,exe)
    (out/'qa/archive.json').write_text(json.dumps(archive,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    script=Path(__file__).resolve().with_name('smoke_windows_main.py')
    command=[sys.executable,'-X','utf8','-B',str(script),'--source',str(source),'--exe',str(exe),
             '--out',str(exe.parent/'qa')]
    with (out/'qa/smoke.log').open('wb') as log:
        smoke=subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    require(smoke.returncode==0,'Native EXE smoke failed; inspect qa/smoke.log and package/qa')
    validation=json.loads((exe.parent/'qa/validation.json').read_text(encoding='utf-8'))
    require(validation['success'],'Native EXE validation did not pass')
    require(git(source,'rev-parse','HEAD')==expected_commit,'Source changed while building')
    require(not git(source,'status','--porcelain=v2','--untracked-files=all'),'Tracked/untracked source changed while building')
    source_files={p.relative_to(source).as_posix():digest(p)
                  for p in sorted([*source.glob('*.py'),source/'PescaIdle.spec',source/'requirements.txt',
                                   source/'requirements-build.txt'])}
    utc=datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        local=utc.astimezone(ZoneInfo('America/Sao_Paulo'))
    except (ImportError,KeyError):
        local=utc.astimezone(timezone(timedelta(hours=-3)))
    info=dict(source_commit=expected_commit,source_branch_reference='main',
              source_tree=git(source,'rev-parse','HEAD^{tree}'),source_checkout_clean=True,
              tooling_commit=git(Path(__file__).resolve().parents[1],'rev-parse','HEAD'),
              generated_utc=utc.isoformat(),generated_sao_paulo=local.isoformat(),
              application_version=None,version_note='Desktop source/spec has no explicit application version; no version number was invented.',
              target='Windows x64',build_tool='PyInstaller',versions=versions,
              python=platform.python_version(),build_platform=platform.platform(),
              executable=exe.name,bytes=exe.stat().st_size,sha256=digest(exe),
              source_sha256=source_files,spec_unmodified=True,clean_build=True,
              archive_module_count=archive['module_count'],archive_asset_count=archive['asset_count'],
              validation_success=True,real_save_used=False,
              authenticode_signed=False,limitations=validation['limits'])
    deliver=out/'deliverables';deliver.mkdir()
    shutil.copy2(exe,deliver/exe.name)
    for name,data in [('BUILD.json',info),('VALIDATION.json',validation),('ARCHIVE.json',archive)]:
        (deliver/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (deliver/'SHA256SUMS.txt').write_text(info['sha256']+'  '+exe.name+'\n',encoding='utf-8')
    print(json.dumps({k:info[k] for k in ('source_commit','target','executable','bytes','sha256','validation_success')},ensure_ascii=False))
    return info


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--expected-commit',required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    build(args.source,args.expected_commit,args.out)
