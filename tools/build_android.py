"""Build the shared Qt game on Linux; stage only runtime sources and assets."""
import argparse,configparser,hashlib,json,os,shutil,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION='6.11.2'


def build(output,arch):
    if sys.platform!='linux':raise RuntimeError('O empacotamento Android requer Linux.')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    sdk=Path(os.environ['ANDROID_HOME']);ndk=sdk/'ndk'/'27.2.12479018'
    if not (sdk/'licenses').exists() or not ndk.exists():
        raise RuntimeError('SDK com licenças existentes e NDK 27.2.12479018 são necessários; este script não aceita termos automaticamente.')
    stage=output/'stage';stage.mkdir()
    for source in ROOT.glob('*.py'):shutil.copy2(source,stage/source.name)
    (stage/'tools').mkdir();shutil.copy2(ROOT/'tools/dev_access.py',stage/'tools/dev_access.py')
    for source in (ROOT/'assets').rglob('*'):
        relative=source.relative_to(ROOT/'assets')
        if source.is_file() and source.suffix in ('.png','.json') and 'source' not in relative.parts:
            target=stage/'assets'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    wheels=output/'wheels';wheels.mkdir()
    paths=[]
    for package in ('pyside6','shiboken6'):
        name=f'{package}-{VERSION}-{VERSION}-cp311-cp311-android_{arch}.whl'
        target=wheels/name
        urllib.request.urlretrieve(f'https://download.qt.io/official_releases/QtForPython/{package}/{name}',target)
        paths.append(target)
    env=os.environ.copy();env['PESCA_IDLE_SAVE_PATH']=str(output/'synthetic-profile.json')
    env['APPDATA']=str(output/'qa-appdata');env['LOCALAPPDATA']=str(output/'qa-localappdata')
    subprocess.run(['pyside6-android-deploy','--init','--name','PescaIdle','--wheel-pyside',str(paths[0]),'--wheel-shiboken',str(paths[1]),'--ndk-path',str(ndk),'--sdk-path',str(sdk),'--extra-modules','Core,Gui,Widgets','--keep-deployment-files','--force'],cwd=stage,env=env,check=True)
    spec=stage/'buildozer.spec';cfg=configparser.ConfigParser(interpolation=None);cfg.read(spec)
    options={'package.name':'pescaidle','package.domain':'br.com.bernardoj','version':'2.1.0',
        'source.include_exts':'py,png,json','source.exclude_dirs':'.git,.venv,__pycache__',
        'requirements':'python3==3.11.11,hostpython3==3.11.11,shiboken6,PySide6',
        'android.api':'36','android.minapi':'28','android.ndk':'27c','android.ndk_api':'28',
        'android.accept_sdk_license':'False','android.skip_update':'True','android.permissions':'',
        'android.numeric_version':'21000','android.debug_artifact':'apk','android.release_artifact':'apk',
        'orientation':'all','fullscreen':'0','p4a.branch':'develop',
        'p4a.commit':'94ffd5f31d816414ad1fe66c0fe587c61daac757'}
    for key,value in options.items():cfg.set('app',key,value)
    cfg.set('buildozer','bin_dir',str(output/'bin'))
    with spec.open('w') as f:cfg.write(f)
    mode='release' if arch=='aarch64' else 'debug'
    subprocess.run([sys.executable,'-m','buildozer','-v','android',mode],cwd=stage,env=env,check=True)
    apk=list((output/'bin').glob('*.apk'))
    if len(apk)!=1:raise RuntimeError('APK único não encontrado após compilação.')
    target=output/f'PescaIdle-{arch}-unsigned.apk';shutil.copy2(apk[0],target)
    source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (output/'build.json').write_text(json.dumps({'source_commit':source_sha,'qt':VERSION,'arch':arch,
        'wheels':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'apk_sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2),encoding='utf-8')
    print('APK gerado:',target)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--arch',choices=['aarch64','x86_64'],default='aarch64')
    args=parser.parse_args();build(args.output,args.arch)
