"""Record final APK identities without collecting profiles or signing material."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
from zoneinfo import ZoneInfo


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve(strict=True)
    original=json.loads((out/'build.json').read_text(encoding='utf-8'))
    now=datetime.now(timezone.utc)
    files={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())
           for p in sorted(out.glob('PescaIdle-*.apk'))}
    report=dict(source_commit=original['source_commit'],source_branch=subprocess.check_output(
        ['git','symbolic-ref','--short','HEAD'],text=True).strip() if not subprocess.run(
        ['git','symbolic-ref','-q','HEAD'],stdout=subprocess.DEVNULL).returncode else 'detached CI checkout',
        source_main_base='f8190f5e6a7b2690a6d00eb8f1ef727cfe0bba34',
        platform='Android '+original['arch'],generated_utc=now.isoformat(),
        generated_sao_paulo=now.astimezone(ZoneInfo('America/Sao_Paulo')).isoformat(),
        app_version='2.1.0',version_code=21000,python=platform.python_version(),qt=original['qt'],
        p4a_commit=original['p4a_commit'],ndk='27.2.12479018',
        build_tool='pyside6-android-deploy / Buildozer 1.5.0 / python-for-android',
        qa_package=original['qa_package'],files=files,
        distribution_note=(out/'distribution.txt').read_text(encoding='utf-8').strip(),
        native_validation='Pending separate emulator job; this manifest does not certify execution.',
        hardware_limits='No physical ARM64 or 16 KB-page-device test in this pipeline.')
    (out/'BUILD-FINAL.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(source_commit=report['source_commit'],files=files),indent=2))


if __name__=='__main__':main()
