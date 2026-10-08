"""Install the QA APK on a disposable AVD; collect on-device results and pixels."""
import argparse,getpass,json,os,struct,subprocess,time,uuid
from pathlib import Path


def call(*args,timeout=60):
    return subprocess.check_output(args,timeout=timeout,text=True,stderr=subprocess.STDOUT)


def test(apk,out):
    apk=Path(apk).resolve()
    if apk.is_dir():
        candidates=list(apk.rglob('PescaIdle-x86_64.apk'))
        if len(candidates)!=1:raise RuntimeError('QA APK unique file not found')
        apk=candidates[0]
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    # avdmanager and emulator disagree about the runner's default AVD directory.
    # Both must use this task's disposable directory, without changing ~/.android.
    avd_home=out/'avd';avd_home.mkdir()
    os.environ['ANDROID_AVD_HOME']=str(avd_home)
    user_home=out/'android-user';user_home.mkdir()
    os.environ['ANDROID_USER_HOME']=str(user_home)
    sdk=Path(os.environ['ANDROID_HOME']);adb=str(sdk/'platform-tools/adb')
    image='system-images;android-35;google_apis;x86_64'
    call(str(sdk/'cmdline-tools/latest/bin/sdkmanager'),'--install','emulator',image,timeout=300)
    avd='pesca-'+uuid.uuid4().hex
    subprocess.run([str(sdk/'cmdline-tools/latest/bin/avdmanager'),'create','avd','-n',avd,'-k',image,'--device','pixel_2'],input='no\n',text=True,check=True,timeout=60)
    assert avd in call(str(sdk/'emulator/emulator'),'-list-avds')
    log=(out/'emulator.log').open('w')
    command=[str(sdk/'emulator/emulator'),'-avd',avd,'-no-window','-no-audio','-no-boot-anim','-no-snapshot','-no-metrics','-gpu','swiftshader_indirect']
    if not os.access('/dev/kvm',os.R_OK|os.W_OK):
        # Existing runner privilege, scoped to this process and the same UID.
        # No chmod, udev rule, group membership or system configuration changes.
        command=['sudo','-n','--','runuser','-u',getpass.getuser(),'-g','kvm','--','env',
                 'ANDROID_AVD_HOME='+str(avd_home),'ANDROID_USER_HOME='+str(user_home),
                 'ANDROID_HOME='+str(sdk),*command]
    emu=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    package='br.com.bernardoj.pescaidle.qa'
    try:
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            if emu.poll() is not None:raise RuntimeError('Emulator exited; see emulator.log')
            if '\tdevice' in call(adb,'devices'):break
            time.sleep(2)
        else:raise RuntimeError('Emulator did not connect; see emulator.log')
        deadline=time.monotonic()+240
        while time.monotonic()<deadline:
            if call(adb,'shell','getprop','sys.boot_completed').strip()=='1':break
            time.sleep(3)
        else:raise RuntimeError('AVD did not finish booting')
        call(adb,'shell','input','keyevent','82')
        call(adb,'install','-r',str(Path(apk).resolve()),timeout=120)
        call(adb,'logcat','-c')
        call(adb,'shell','am','start','-W','-n',package+'/org.kivy.android.PythonActivity',timeout=60)
        deadline=time.monotonic()+180;report=None
        while time.monotonic()<deadline:
            logs=call(adb,'logcat','-d')
            (out/'logcat.txt').write_text(logs,encoding='utf-8')
            for line in logs.splitlines():
                if 'PESCA_QA_RESULT=' in line:
                    report=json.loads(line.split('PESCA_QA_RESULT=',1)[1]);break
            if report:break
            time.sleep(3)
        if not report:raise RuntimeError('Android QA did not return a result; see logcat.txt')
        (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        assert report['passed'],report.get('error',report)
        profile=Path(report['profile']);private=str(profile.parent)
        for filename in ('game.png','shop.png','collection.png','travel.png','expedition.png'):
            with (out/filename).open('wb') as f:subprocess.run([adb,'exec-out','run-as',package,'cat',private+'/'+filename],stdout=f,check=True,timeout=30)
        call(adb,'shell','settings','put','system','accelerometer_rotation','1')
        for orientation,value in [('portrait','0:9.8:0'),('landscape','9.8:0:0')]:
            call(adb,'emu','sensor','set','acceleration',value)
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                png=subprocess.check_output([adb,'exec-out','screencap','-p'],timeout=30)
                width,height=struct.unpack_from('>II',png,16)
                if (width>height)==(orientation=='landscape'):break
                time.sleep(1)
            else:raise RuntimeError('Actual screen did not rotate to '+orientation)
            (out/(orientation+'-screen.png')).write_bytes(png)
        # A real Android background transition and return, not just a Qt signal.
        call(adb,'shell','input','keyevent','3');time.sleep(2)
        call(adb,'shell','am','start','-W','-n',package+'/org.kivy.android.PythonActivity');time.sleep(2)
        assert call(adb,'shell','pidof',package).strip()
        with (out/'resume-screen.png').open('wb') as f:subprocess.run([adb,'exec-out','screencap','-p'],stdout=f,check=True,timeout=30)
        report['host_checks']=['APK installed','portrait/landscape display','real background/resume process alive']
        report['android_api']=call(adb,'shell','getprop','ro.build.version.sdk').strip()
        (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('On-device Android checks passed:',len(report['checks']),'+',len(report['host_checks']))
    finally:
        if emu.poll() is None:
            subprocess.run([adb,'shell','am','force-stop',package],timeout=20)
            subprocess.run([adb,'emu','kill'],timeout=20)
            try:emu.wait(timeout=30)
            except subprocess.TimeoutExpired:emu.terminate();emu.wait(timeout=10)
        log.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('apk');parser.add_argument('--output',required=True)
    args=parser.parse_args();test(args.apk,args.output)
