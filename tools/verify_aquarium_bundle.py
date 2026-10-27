"""Inspect a NEW visual-demo EXE without running game code or reading profiles."""
import argparse
import hashlib
import json
import marshal
from pathlib import Path
import types
from PyInstaller.archive.readers import CArchiveReader

ROOT=Path(__file__).resolve().parents[1]


def canonical(code):
    constants=tuple(canonical(c) if isinstance(c,types.CodeType) else c for c in code.co_consts)
    return code.replace(co_filename='<source>',co_consts=constants)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();out=args.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out.exists():raise ValueError('Use um JSON novo em qa/.')
    exe=args.exe.resolve(strict=True)
    if not exe.is_relative_to(ROOT/'dist'):raise ValueError('Verifique somente uma build em dist/.')
    archive=CArchiveReader(str(exe));pyz=archive.open_embedded_archive('PYZ.pyz')
    info=json.loads(archive.extract('aquario_build.json'))
    modules=['pesca_museu_visual','pesca_museu_ui','pesca_tamanho_visual',
             'pesca_especies_visual','pesca_catalogo','pesca_tamanhos','tools.aquarium_preview']
    for name in modules:
        path=ROOT/(name.replace('.','/')+'.py')
        expected=canonical(compile(path.read_bytes(),str(path),'exec',dont_inherit=True))
        actual=canonical(pyz.extract(name))
        if marshal.dumps(expected)!=marshal.dumps(actual):raise AssertionError('Bytecode difere: '+name)
    assets=[]
    for name,digest in info['files'].items():
        if name.startswith('assets/'):
            if hashlib.sha256(archive.extract(name.replace('/','\\'))).hexdigest()!=digest:
                raise AssertionError('Asset difere: '+name)
            assets.append(name)
    forbidden=['pesca_idle','pesca_pescaria','pesca_save','pesca_offline']
    if any(name in pyz.toc for name in forbidden):raise AssertionError('Motor/save incluído na demonstração visual.')
    result=dict(source_commit=info['source_commit'],modules_verified=modules,
        asset_count=len(assets),engine_and_persistence_modules_absent=True,
        executable=exe.name,bytes=exe.stat().st_size,sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
