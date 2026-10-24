"""Exhaustive finite context matrix, synthetic contracts and visual weather QA."""
import argparse,ast,csv,hashlib,json,os,platform,statistics,sys,time,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--core-only',action='store_true');args=ap.parse_args();out=args.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out==ROOT/'qa':ap.error('Use pasta nova dentro de qa deste candidato.')
    out.mkdir(parents=True,exist_ok=False)
    for child in ['tmp','profiles','appdata','localappdata','images']:(out/child).mkdir()
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(out/'profiles'/'guard.json'),APPDATA=str(out/'appdata'),
        LOCALAPPDATA=str(out/'localappdata'),TEMP=str(out/'tmp'),TMP=str(out/'tmp'),QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0,str(ROOT))
    from tools import test_climate
    with (out/'contracts.log').open('w',encoding='utf-8') as log:
        tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_climate))
    result=dict(python=platform.python_version(),tests=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors),
        profile_isolated=True,source_base='c545ca652386d74372307bd6d52a91f84d1ed4a0')
    if tests.failures or tests.errors:
        (out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result);return 1
    print(f'Contratos: {tests.testsRun} passaram.',flush=True)
    if args.core_only:
        (out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return 0
    from pesca_catalogo import ESPECIES,LOCAIS,OCORRENCIAS,eligible,probabilities
    from pesca_clima import IDS,factor,affinities,DATA
    from pesca_tempo import PERIODOS,snapshot
    from pesca_moedas import reward
    contexts=0;money_rows=0;unchanged=[];direction_errors=[];expected_changes=[]
    with (out/'economy-contexts.csv').open('w',encoding='utf-8',newline='') as csvfile:
        writer=csv.writer(csvfile);writer.writerow(['map','period','weather','rod','boat','base_cents_per_event','weather_cents_per_event','relative_change_percent'])
        for mid in LOCAIS:
            for pid,_,_,_ in PERIODOS:
                fish={o['species_id'] for o in eligible(mid,pid,'peixe')};special={o['species_id'] for o in eligible(mid,pid,'especial')}
                assert len(fish)>=3
                for rod in range(11):
                    base=probabilities(mid,pid,rod)
                    for weather in IDS:
                        probs=probabilities(mid,pid,rod,weather);contexts+=1
                        assert set(probs)==set(base) and all(0<p<=1 for p in probs.values())
                        assert abs(sum(probs.values())-1)<1e-12 and probs['bota_velha']==base['bota_velha']
                        assert all(id_ in fish|special|{'bota_velha'} for id_ in probs)
                        if weather=='ameno':assert probs==base
                        for pool in (fish,special):
                            if not pool:continue
                            share=sum(base[id_] for id_ in pool);weighted=sum(base[id_]*factor(mid,id_,weather,pid) for id_ in pool)
                            assert abs(sum(probs[id_] for id_ in pool)-share)<1e-12
                            for id_ in pool:
                                expected=share*base[id_]*factor(mid,id_,weather,pid)/weighted
                                assert abs(probs[id_]-expected)<1e-12
                                f=factor(mid,id_,weather,pid);delta=probs[id_]-base[id_]
                                if f!=1:
                                    if abs(delta)<1e-14:unchanged.append([mid,pid,rod,weather,id_])
                                    elif (f>1)!=(delta>0):direction_errors.append([mid,pid,rod,weather,id_,f,delta])
                        for boat in range(11):
                            old=sum(p*reward(ESPECIES[id_]['valor'],boat) for id_,p in base.items() if id_ in ESPECIES)
                            new=sum(p*reward(ESPECIES[id_]['valor'],boat) for id_,p in probs.items() if id_ in ESPECIES)
                            percent=100*(new/old-1);expected_changes.append(percent)
                            writer.writerow([mid,pid,weather,rod,boat,old,new,percent]);money_rows+=1
    result.update(contexts=contexts,economic_contexts=money_rows,direction_errors=direction_errors,
        canceled_by_normalization=unchanged,min_expected_income_change_percent=min(expected_changes),max_expected_income_change_percent=max(expected_changes))
    assert not direction_errors, direction_errors[:3]
    print(f'Matriz: {contexts} pools, {money_rows} contextos econômicos; direções conferidas.',flush=True)
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPainter,QImage,QColor,QFont
    from PySide6.QtCore import Qt,QTimer,QEvent
    from PySide6.QtTest import QTest
    from pesca_idle import JogoPesca
    from pesca_ui import configure_app
    from pesca_clima_ui import ClimateDialog,current_weather
    from pesca_plataforma import fit_dialog
    app=QApplication.instance() or QApplication([]);configure_app(app)
    wall=[test_climate.START];g=JogoPesca(wall_clock=lambda:wall[0],monotonic_clock=lambda:0)
    g.relogio.stop();g.timer_save.stop();g.pausado=True;g.popup=None;g._popup_queue=[]
    g.estado['vara']=g.estado['barco']=10
    from pesca_catalogo import desbloquear
    desbloquear(g.estado);g.show();app.processEvents()
    images=0;frames=0;pixel_differences=[];baseline_rng=g.estado['rng_state']
    hours=[6,8,10,12,15,18,23]
    for (pid,_,_,_),hour in zip(PERIODOS,hours):
        sheet=QImage(1300,1530,QImage.Format_RGB32);sheet.fill(QColor('#172d40'));p=QPainter(sheet)
        font=QFont('Segoe UI');font.setPixelSize(13);p.setFont(font);p.setPen(QColor('#f4ddad'))
        for wi,weather in enumerate(IDS):p.drawText(wi*260+8,23,DATA['climates'][wi]['name']+' / '+pid)
        for mi,mid in enumerate(LOCAIS):
            y=40+mi*184;g.estado['local_atual_id']=mid
            g._preview_clock=datetime(2026,10,23,hour,tzinfo=timezone(timedelta(hours=-3)))
            g._clock_snapshot=snapshot(g._preview_clock.timestamp(),-10800);g.fase=2
            g._preview_weather='ameno';baseline=g._render.render(g)[0]
            for wi,weather in enumerate(IDS):
                g._preview_weather=weather;image=g._render.render(g)[0]
                assert not image.isNull() and (image.width(),image.height())==(256,144)
                changed=sum(image.pixel(x,y)!=baseline.pixel(x,y) for y in range(144) for x in range(256))
                if weather!='ameno':assert changed>10,(mid,pid,weather)
                else:assert changed==0
                pixel_differences.append(dict(map=mid,period=pid,weather=weather,changed_pixels=changed))
                p.drawImage(wi*260+2,y,image);p.drawText(wi*260+4,y+162,LOCAIS[mid]['nome'])
                for phase in (.0,.5,5,16):
                    g.fase=phase;assert not g._render.render(g)[0].isNull();frames+=1
                g.fase=2;images+=1
        p.end();assert sheet.save(str(out/'images'/('matriz-'+pid+'.png')))
    ui_checks=0
    for weather in IDS:
        g._preview_weather=weather;g._preview_clock=datetime(2026,10,23,12,tzinfo=timezone(timedelta(hours=-3)))
        g._clock_snapshot=snapshot(g._preview_clock.timestamp(),-10800);g._sync_climate_button()
        assert g.botao_clima.toolTip().startswith('Clima: '+DATA['climates'][IDS.index(weather)]['name'])
        assert g.grab().save(str(out/'images'/('hud-'+weather+'.png')))
        dialog=ClimateDialog(g);dialog.show();app.processEvents()
        detail_color=dialog.detail.grab().toImage().pixelColor(1,1)
        assert not (detail_color.red()>230 and detail_color.green()>230 and detail_color.blue()>230)
        for mid in [None,*LOCAIS]:
            dialog.map.setCurrentIndex(dialog.map.findData(mid));app.processEvents()
            assert dialog.list.count()>0;ui_checks+=1
        dialog.map.setCurrentIndex(0);dialog.grab().save(str(out/'images'/('painel-'+weather+'.png')))
        before=copy_state(g.estado)
        dialog.accept();assert not dialog.timer.isActive();dialog.deleteLater();app.processEvents()
        assert g.estado==before
    opened=[]
    def close_clicked():
        for widget in app.topLevelWidgets():
            if isinstance(widget,ClimateDialog) and widget.isVisible():opened.append(widget.windowTitle());widget.accept()
    QTimer.singleShot(60,close_clicked);QTest.mouseClick(g.botao_clima,Qt.LeftButton)
    assert opened==['Clima de hoje'] and not g._arrastando
    QTimer.singleShot(60,close_clicked);g.botao_clima.setFocus();QTest.keyClick(g.botao_clima,Qt.Key_Space)
    assert len(opened)==2
    os.environ['PESCA_IDLE_MOBILE']='1';configure_app(app)
    g.setMinimumSize(0,0);g.setMaximumSize(16777215,16777215);g.resize(320,568);g._fit_mobile_viewport();app.processEvents()
    assert g.rect_clima.width()>=44 and not g.rect_clima.intersects(g.rect_icone)
    for weather in IDS:
        g._preview_weather=weather;g._sync_climate_button();g.grab().save(str(out/'images'/('mobile-'+weather+'.png')))
        dialog=ClimateDialog(g);fit_dialog(dialog);dialog.resize(320,568);dialog.show();app.processEvents()
        assert dialog.icon.width()==40 and dialog.icon.height()==40
        assert not dialog.icon.geometry().intersects(dialog.heading.geometry())
        dialog.grab().save(str(out/'images'/('painel-mobile-'+weather+'.png')));dialog.accept();dialog.deleteLater();app.processEvents()
    os.environ.pop('PESCA_IDLE_MOBILE');g.resize_viewport()
    timings={}
    for weather in IDS:
        g._preview_weather=weather;g.estado['local_atual_id']='mar_das_auroras';g._preview_clock=datetime(2026,10,23,12,tzinfo=timezone(timedelta(hours=-3)))
        for _ in range(5):g._render.render(g)
        values=[]
        for n in range(60):
            g.fase=n/10;start=time.perf_counter();g._render.render(g);values.append((time.perf_counter()-start)*1000)
        timings[weather]=dict(median_ms=statistics.median(values),p95_ms=sorted(values)[56],max_ms=max(values))
    assert g.estado['rng_state']==baseline_rng
    g.relogio.stop();g.timer_save.stop();g._store.close();g._closed=True;g.close()
    result.update(rendered_scenes=images,additional_animation_frames=frames,ui_filter_cases=ui_checks,
        click_and_keyboard=True,mobile_viewport=[320,568],native_android_tested=False,timings=timings,
        pixel_differences=pixel_differences,success=True)
    result['source_sha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted([*ROOT.glob('pesca*.py'),ROOT/'assets/clima_especies.json',*ROOT.glob('tools/*clima*.py'),*ROOT.glob('tools/*climate*.py')])}
    (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Visual: {images} cenas e {frames} quadros; interface e clique aprovados.',flush=True)
    return 0

def copy_state(state):
    import copy
    return copy.deepcopy(state)

if __name__=='__main__':raise SystemExit(main())
