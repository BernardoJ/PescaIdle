"""Frozen weather smoke in three processes with an explicitly isolated profile."""
import copy,hashlib,json,os,sys,traceback
from pathlib import Path
from pesca_piloto import validate_profile_path

def run():
    out=validate_profile_path(os.environ['PESCA_IDLE_CLIMATE_QA_DIR']);out.mkdir(parents=True,exist_ok=True)
    mode=sys.argv[sys.argv.index('--climate-smoke')+1]
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt,QTimer
        from PySide6.QtTest import QTest
        from pesca_idle import JogoPesca,ESTADO_PADRAO
        from pesca_ui import configure_app
        from pesca_save import migrate
        from pesca_clima import IDS,new_climate
        from pesca_clima_ui import ClimateDialog,current_weather
        from pesca_pescaria import FishingEngine
        from pesca_tamanhos import empty_sizes
        from pesca_catalogo import desbloquear
        from pesca_tempo import snapshot
        import random
        start=1792810799. # 23/10/2026 23:59:59 UTC-3
        now=start if mode=='pending' else start+2
        app=QApplication([]);configure_app(app);g=JogoPesca(wall_clock=lambda:now,monotonic_clock=lambda:0)
        g.setAttribute(Qt.WA_DontShowOnScreen,True);g.relogio.stop();g.timer_save.stop();g.pausado=True;g.show();app.processEvents()
        g._clock_snapshot=snapshot(now,-10800)
        if mode=='pending':
            assert not g.estado['inventario_por_id']
            s=migrate({},ESTADO_PADRAO,start);s['perfil_id']='climate-frozen-fixture'
            s['medidas_peixes']=empty_sizes(s['perfil_id']);s['clima']=new_climate(s['perfil_id'],start)
            s['rng_state']=random.Random(18).getstate();s['contexto_fuso']=-10800;s['pausado']=True
            engine=FishingEngine(s);event=engine.begin_strike(start,-10800)
            assert g._commit(engine.advance(0,start,-10800))
            data=dict(pending=copy.deepcopy(event),clima=copy.deepcopy(s['clima']),balance=s['moedas_centavos'])
        elif mode=='deliver':
            old=json.loads((out/'pending.json').read_text(encoding='utf-8'))['data'];event=copy.deepcopy(g.estado['pesca_pendente'])
            assert event==old['pending'];assert current_weather(g)['data']!=event['context']['clima']['data']
            g.sortear();assert g._last_result['context']==event['context']
            assert g.estado['moedas_centavos']==old['balance']+event['gain_cents']
            assert g.estado['clima']==old['clima']
            for weather in IDS:
                g._preview_weather=weather;g._sync_climate_button();g.grab().save(str(out/('exe-'+weather+'.png')))
                dialog=ClimateDialog(g);dialog.show();app.processEvents();dialog.grab().save(str(out/('exe-painel-'+weather+'.png')))
                dialog.accept();dialog.deleteLater()
            g._preview_weather=None;g._sync_climate_button()
            data=dict(clima=copy.deepcopy(g.estado['clima']),balance=g.estado['moedas_centavos'],inventory=copy.deepcopy(g.estado['inventario_por_id']),
                      measurements=copy.deepcopy(g.estado['medidas_peixes']),applied=g.estado['ultimo_evento_aplicado'])
        elif mode=='reopen':
            expected=json.loads((out/'deliver.json').read_text(encoding='utf-8'))['data']
            for key,target in [('clima','clima'),('moedas_centavos','balance'),('inventario_por_id','inventory'),('medidas_peixes','measurements'),('ultimo_evento_aplicado','applied')]:
                assert g.estado[key]==expected[target],key
            opened=[]
            def close_dialog():
                for item in app.topLevelWidgets():
                    if isinstance(item,ClimateDialog) and item.isVisible():opened.append(True);item.accept()
            QTimer.singleShot(70,close_dialog);QTest.mouseClick(g.botao_clima,Qt.LeftButton);assert opened
            data=dict(reopen_kept_progress=True,click=True,clima=copy.deepcopy(g.estado['clima']))
        else:raise ValueError('Modo de smoke desconhecido.')
        g.salvar();g._store.close();g._closed=True;g.close()
        (out/(mode+'.json')).write_text(json.dumps(dict(frozen=bool(getattr(sys,'frozen',False)),schema=g.estado['schema_version'],data=data),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return 0
    except Exception:
        (out/(mode+'-error.txt')).write_text(traceback.format_exc(),encoding='utf-8');return 1
