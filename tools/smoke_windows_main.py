"""Validate a freshly built, provenance-checked EXE on native Windows only.

The executable and every profile are disposable. No real save is read. Source
imports are limited to this exact checkout; its bytecode is separately checked
against the executable by build_windows_main.py.
"""
import argparse
import ast
import copy
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def native_helpers(source):
    spec = importlib.util.spec_from_file_location('native_close_helpers', source/'tools/test_windows_close.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def windows_for_process(process, helpers):
    from ctypes import wintypes as W
    user = ctypes.windll.user32
    callback = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
    user.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
    user.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
    user.GetClassNameW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
    rows = []
    pids = helpers.family(process.pid)
    def visit(handle, unused):
        pid = W.DWORD()
        user.GetWindowThreadProcessId(handle, ctypes.byref(pid))
        if pid.value in pids:
            title = ctypes.create_unicode_buffer(1024)
            kind = ctypes.create_unicode_buffer(256)
            user.GetWindowTextW(handle, title, len(title))
            user.GetClassNameW(handle, kind, len(kind))
            rows.append((handle, title.value, kind.value))
        return True
    user.EnumWindows(callback(visit), 0)
    return rows


def run_exe(exe, arguments, env, cwd, log, helpers, reject=False, cancel_recovery=False):
    from ctypes import wintypes as W
    seen_recovery = False
    closed_error = False
    with log.open('wb') as output:
        process = subprocess.Popen([str(exe), *arguments], cwd=cwd, env=env,
                                   stdout=output, stderr=subprocess.STDOUT)
        deadline = time.monotonic()+100
        try:
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    raise RuntimeError('EXE timed out: '+log.name)
                if reject:
                    for handle, title, kind in windows_for_process(process, helpers):
                        is_recovery = title == 'Recuperar progresso'
                        # Close only a modal owned by the spawned process. Closing
                        # the recovery question is the explicit No/cancel path.
                        if is_recovery and cancel_recovery:
                            seen_recovery = True
                        elif kind == '#32770':
                            closed_error = True
                        else:
                            continue
                        ctypes.windll.user32.PostMessageW.argtypes = [W.HWND,W.UINT,W.WPARAM,W.LPARAM]
                        ctypes.windll.user32.PostMessageW(handle, 0x10, 0, 0)
                time.sleep(.15)
            return dict(exit_code=process.returncode, recovery_prompt_seen=seen_recovery,
                        owned_bootloader_error_dialog_closed=closed_error)
        finally:
            if process.poll() is None:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                               capture_output=True, timeout=20, check=False)


def run(source, exe, out):
    require(os.name == 'nt', 'Native Windows is required; no Linux result is a Windows approval.')
    source = source.resolve(strict=True)
    exe = exe.resolve(strict=True)
    out = out.resolve()
    require(out.is_relative_to(exe.parent) and not out.exists(), 'Use a NEW QA directory inside the EXE folder.')
    out.mkdir(parents=True)
    for name in ('foreign-cwd','tmp','appdata','localappdata'):
        (out/name).mkdir()
    env = os.environ.copy()
    for key in ('PYTHONHOME','PYTHONPATH','VIRTUAL_ENV','PESCA_IDLE_MOBILE','PESCA_IDLE_DEMO_DIR'):
        env.pop(key, None)
    system_root = os.environ.get('SystemRoot', r'C:\Windows')
    env.update(PATH=os.pathsep.join([str(Path(system_root)/'System32'),system_root]),
               TEMP=str(out/'tmp'), TMP=str(out/'tmp'), APPDATA=str(out/'appdata'),
               LOCALAPPDATA=str(out/'localappdata'), QT_QPA_PLATFORM='windows',
               PYTHONDONTWRITEBYTECODE='1')
    helpers = native_helpers(source)
    results = []

    # Actual EXE startup, assets, all maps, v1 migration, UI and OS Qt backend.
    for scale in ('1','1.25'):
        case = out/('startup-'+scale.replace('.','-'))
        case.mkdir()
        path = case/'save.json'
        original = json.dumps(dict(moedas=12.34, vara=0, barco=0, total_pescados=10,
                              inventario={'Lambari':10}, ultimo_salvo=time.time())).encode('utf-8')
        path.write_bytes(original)
        evidence = case/'evidence'
        current = dict(env, PESCA_IDLE_SAVE_PATH=str(path), PESCA_IDLE_SMOKE_DIR=str(evidence),
                       QT_SCALE_FACTOR=scale)
        execution = run_exe(exe, ['--smoke-test'], current, out/'foreign-cwd', case/'process.log', helpers)
        require(execution['exit_code']==0, 'Startup smoke failed at scale '+scale)
        report = json.loads((evidence/'resultado.json').read_text(encoding='utf-8'))
        require(report['frozen'] and report['schema']==5 and report['maps']==8, 'Wrong frozen build/schema/maps')
        require(report['assets'] and report['ui_icon'] and report['cosmetic_sprites']>0, 'Missing packaged assets/UI')
        require(report['scene']==[256,144] and report['light_plates']==96, 'Unexpected scene/lighting')
        require(report['legacy_inventory']==10, 'Legacy inventory was not preserved')
        require(path.with_name('save.pre-expansao-v1.json').read_bytes()==original, 'Migration backup differs')
        require(len(list(evidence.glob('*-executavel.png'))) >= 8, 'Missing render evidence')
        results.append(dict(test='native-startup-assets-and-v1-migration',scale=scale,passed=True))

    # The production entry already supports this frozen smoke. Keep profile and
    # output inside EXE.parent, but run from a foreign directory without Python.
    case = out/'climate';case.mkdir()
    evidence = case/'evidence'
    for mode in ('pending','deliver','reopen'):
        current = dict(env,PESCA_IDLE_SAVE_PATH=str(case/'save.json'),
                       PESCA_IDLE_CLIMATE_QA_DIR=str(evidence))
        execution = run_exe(exe,['--climate-smoke',mode],current,out/'foreign-cwd',case/(mode+'.log'),helpers)
        require(execution['exit_code']==0,'Frozen climate smoke failed: '+mode)
        report = json.loads((evidence/(mode+'.json')).read_text(encoding='utf-8'))
        require(report['frozen'] and report['schema']==5,'Climate smoke did not run frozen schema 5')
        results.append(dict(test='native-frozen-climate-'+mode,passed=True))

    # Source fixtures are generated without importing the game/GUI. Store tests
    # below use source/qa because the desktop boundary must remain enforced.
    sys.path.insert(0,str(source))
    from pesca_save import SaveStore, SaveError, migrate
    tree = ast.parse((source/'pesca_idle.py').read_text(encoding='utf-8'))
    defaults = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                    and any(isinstance(t,ast.Name) and t.id=='ESTADO_PADRAO' for t in n.targets))
    now = 1792810801.
    valid = migrate({},defaults,now);valid['pausado']=True
    invalid = copy.deepcopy(valid);invalid.pop('clima')
    runtime_defaults = migrate({},defaults,now-1000)
    for valid_backup in (False,True):
        case = out/('missing-climate-valid-backup' if valid_backup else 'missing-climate-invalid-backup');case.mkdir()
        path = case/'save.json';original=json.dumps(invalid,ensure_ascii=False,indent=3).encode('utf-8');path.write_bytes(original)
        backup = json.dumps(valid).encode('utf-8') if valid_backup else b'synthetic invalid backup sentinel'
        path.with_suffix('.json.bak').write_bytes(backup)
        current = dict(env,PESCA_IDLE_SAVE_PATH=str(path),PESCA_IDLE_SMOKE_DIR=str(case/'evidence'))
        execution = run_exe(exe,['--smoke-test'],current,out/'foreign-cwd',case/'process.log',helpers,
                            reject=True,cancel_recovery=valid_backup)
        require(execution['exit_code']!=0,'EXE accepted schema 5 without clima')
        require(path.read_bytes()==original,'EXE changed rejected save')
        require(path.with_suffix('.json.bak').read_bytes()==backup,'EXE changed existing backup')
        require(not list(case.glob('save.rejeitado-*.json')),'EXE recovered without consent')
        if valid_backup:require(execution['recovery_prompt_seen'],'EXE did not ask before recovery')
        results.append(dict(test='native-exe-missing-climate-rejected',valid_backup=valid_backup,
                            passed=True,**execution))

    # Exercise the frozen SaveStore and native Windows file-link semantics. The
    # foreign profile is synthetic and deliberately OUTSIDE the EXE boundary;
    # its valid contents must never become a recoverable backup for this pilot.
    case=out/'auxiliary-backup-link';case.mkdir()
    path=case/'save.json'
    original=json.dumps(invalid,ensure_ascii=False,indent=3).encode('utf-8')
    path.write_bytes(original)
    foreign_dir=exe.parent.parent/'foreign-backup-profile-synthetic'
    foreign_dir.mkdir(exist_ok=False)
    foreign=foreign_dir/'save.json';foreign_bytes=json.dumps(valid).encode('utf-8')
    foreign.write_bytes(foreign_bytes)
    require(not foreign.resolve().is_relative_to(exe.parent), 'Foreign fixture must be outside the EXE boundary')
    alias=path.with_suffix('.json.bak')
    try:
        alias.symlink_to(foreign)
    except OSError as exc:
        raise RuntimeError('Native Windows file-symlink creation unavailable; auxiliary isolation is NOT validated. No permissions were changed.') from exc
    require(alias.is_symlink(), 'Native Windows backup link was not created')
    link_target=os.readlink(alias)
    current=dict(env,PESCA_IDLE_SAVE_PATH=str(path),PESCA_IDLE_SMOKE_DIR=str(case/'evidence'))
    execution=run_exe(exe,['--smoke-test'],current,out/'foreign-cwd',case/'process.log',helpers,
                      reject=True,cancel_recovery=True)
    require(execution['exit_code']!=0, 'EXE accepted a rejected save with a foreign backup link')
    require(not execution['recovery_prompt_seen'], 'EXE offered recovery from a foreign-context backup link')
    require(path.read_bytes()==original, 'EXE overwrote the rejected main through a foreign backup link')
    require(alias.is_symlink() and os.readlink(alias)==link_target, 'EXE removed or replaced the foreign backup link')
    require(foreign.read_bytes()==foreign_bytes, 'EXE modified the foreign synthetic profile')
    require(not list(case.glob('save.rejeitado-*.json')), 'EXE archived a save for a foreign backup recovery')
    results.append(dict(test='native-exe-foreign-backup-link-rejected',passed=True,
                        foreign_fixture_outside_exe_boundary=True,synthetic_only=True,**execution))

    source_qa = source/'qa'/('windows-frozen-store-'+str(os.getpid()))
    source_qa.mkdir(parents=True,exist_ok=False)
    for version in (4,5):
        case=source_qa/str(version);case.mkdir();path=case/'save.json'
        state=copy.deepcopy(valid);state['schema_version']=version
        if version==4:state.pop('clima')
        original=json.dumps(state,indent=3).encode('utf-8');path.write_bytes(original)
        with SaveStore(path) as store:
            loaded=store.load(runtime_defaults,now)
            require(loaded['schema_version']==5,'Store did not preserve schema 5')
            if version==4:require(path.with_name('save.pre-schema-4.json').read_bytes()==original,'v4 backup differs')
            stable=path.read_bytes();climate=copy.deepcopy(loaded['clima'])
            require(store.load(runtime_defaults,now+1000)['clima']==climate,'Reload reset climate')
            require(path.read_bytes()==stable,'Reload rewrote a valid v5 file')
        results.append(dict(test='windows-store-migration-and-reopen',input_schema=version,passed=True,
                            execution='source identical to verified packaged pesca_save bytecode'))
    case=source_qa/'recovery';case.mkdir();path=case/'save.json'
    original=json.dumps(invalid).encode('utf-8');path.write_bytes(original)
    backup=json.dumps(valid).encode('utf-8');path.with_suffix('.json.bak').write_bytes(backup)
    with SaveStore(path) as store:
        try:store.load(runtime_defaults,now)
        except SaveError:pass
        else:raise RuntimeError('Source unexpectedly accepted missing weather')
        require(store.backup_available(runtime_defaults,now),'Valid backup unavailable')
        restored=store.recover(runtime_defaults,now)
        require(restored['clima']==valid['clima'],'Recovery changed climate')
    require(next(case.glob('save.rejeitado-*.json')).read_bytes()==original,'Recovery lost rejected bytes')
    require(path.with_suffix('.json.bak').read_bytes()==backup,'Recovery changed valid backup')
    results.append(dict(test='windows-explicit-backup-recovery',passed=True,
                        execution='source identical to verified packaged pesca_save bytecode'))
    report=dict(success=True,platform='native Windows / Qt windows plugin',profile_isolated=True,
                foreign_cwd=True,python_environment_removed_from_exe=True,tests=results,
                real_save_used=False,limits=['Not a clean Windows installation or physical-device/human session.',
                'Positive backup recovery uses source SaveStore with packaged bytecode identity; EXE recovery cancellation is tested.'])
    (out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True);ap.add_argument('--exe',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    result=run(args.source,args.exe,args.out)
    print(json.dumps(dict(success=result['success'],tests=len(result['tests'])),ensure_ascii=False))
