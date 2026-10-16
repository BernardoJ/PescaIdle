"""Exercise native close messages against only the spawned frozen game process."""
import argparse,ctypes,json,os,subprocess,tempfile,time
from ctypes import wintypes as W
from pathlib import Path


def family(root):
    kernel=ctypes.windll.kernel32
    class Entry(ctypes.Structure):
        _fields_=[('dwSize',W.DWORD),('cntUsage',W.DWORD),('pid',W.DWORD),('heap',ctypes.c_size_t),('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),('priority',W.LONG),('flags',W.DWORD),('exe',W.WCHAR*260)]
    kernel.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];kernel.CreateToolhelp32Snapshot.restype=W.HANDLE
    kernel.Process32FirstW.argtypes=[W.HANDLE,ctypes.POINTER(Entry)];kernel.Process32NextW.argtypes=kernel.Process32FirstW.argtypes
    kernel.CloseHandle.argtypes=[W.HANDLE]
    handle=kernel.CreateToolhelp32Snapshot(2,0);entry=Entry();entry.dwSize=ctypes.sizeof(entry);rows=[]
    try:
        ok=kernel.Process32FirstW(handle,ctypes.byref(entry))
        while ok:
            rows.append((entry.pid,entry.parent));ok=kernel.Process32NextW(handle,ctypes.byref(entry))
    finally:kernel.CloseHandle(handle)
    found={root}
    while True:
        more={p for p,parent in rows if parent in found}
        if more<=found:return found
        found|=more


def window(pids):
    user=ctypes.windll.user32;found=[];callback=ctypes.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
    user.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
    user.IsWindowVisible.argtypes=[W.HWND]
    def visit(handle,_):
        pid=W.DWORD();user.GetWindowThreadProcessId(handle,ctypes.byref(pid))
        if pid.value in pids and user.IsWindowVisible(handle):found.append(handle)
        return True
    user.EnumWindows(callback(visit),0)
    return found[0] if found else None


def test(exe,out):
    if os.name!='nt':raise RuntimeError('Windows native test requires Windows')
    checks=[]
    with tempfile.TemporaryDirectory(prefix='pesca-native-close-') as tmp:
        for name,msg,wparam in [('WM_CLOSE',0x10,0),('SC_CLOSE (Alt+F4 path)',0x112,0xF060)]:
            profile=Path(tmp)/(str(msg)+'.json');env=os.environ.copy()
            env.update(PESCA_IDLE_SAVE_PATH=str(profile),APPDATA=tmp,LOCALAPPDATA=tmp,QT_QPA_PLATFORM='windows')
            env.pop('PESCA_IDLE_MOBILE',None)
            process=subprocess.Popen([str(Path(exe).resolve())],cwd=tmp,env=env)
            try:
                deadline=time.monotonic()+30;handle=None
                while time.monotonic()<deadline and process.poll() is None:
                    handle=window(family(process.pid))
                    if handle and profile.exists():break
                    time.sleep(.2)
                assert handle and profile.exists(),'game did not present its window'
                user=ctypes.windll.user32;user.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
                assert user.PostMessageW(handle,msg,wparam,0)
                assert process.wait(timeout=15)==0
                payload=json.loads(profile.read_text(encoding='utf-8'))
                assert payload['schema_version']==3 and type(payload['moedas_centavos']) is int
                # No game import. Opening its writer after process exit proves
                # that the OS lock was released in the distributed executable.
                os.environ['PESCA_IDLE_SAVE_PATH']=str(profile)
                import sys;sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
                from pesca_save import SaveStore
                with SaveStore(profile):pass
                checks.append(name+': process exited, valid save, lock released')
            finally:
                if process.poll() is None:subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=20)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'native-close.json').write_text(json.dumps({'checks':checks,'profile_isolated':True},indent=2),encoding='utf-8')
    print('Native Windows close passed:',len(checks))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('exe');parser.add_argument('--output',required=True)
    args=parser.parse_args();test(args.exe,args.output)
