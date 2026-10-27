"""Focused frozen three-process smoke. Only synthetic candidate profiles."""
from pathlib import Path
import copy,json,os,random,sys,traceback
from pesca_piloto import validate_profile_path

def run():
    output=validate_profile_path(os.environ['PESCA_IDLE_PILOT_QA_DIR']);output.mkdir(parents=True,exist_ok=True)
    mode=sys.argv[sys.argv.index('--pilot-smoke')+1]
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from pesca_idle import JogoPesca,ESTADO_PADRAO,CATALOGO
        from pesca_ui import configure_app
        from pesca_save import migrate
        from pesca_pescaria import FishingEngine
        from pesca_conquistas import grant
        from pesca_museu_ui import MuseuDialog
        import pesca_tamanhos as sizes
        now=1792332000
        app=QApplication(sys.argv);configure_app(app)
        g=JogoPesca(wall_clock=lambda:now,monotonic_clock=lambda:0)
        g.setAttribute(Qt.WA_DontShowOnScreen,True)
        g.relogio.stop();g.timer_save.stop();g.show();app.processEvents()
        g.pausado=True
        if mode=='pending':
            assert not g.estado['inventario_por_id'],'Use um perfil sintético novo.'
            s=migrate({},ESTADO_PADRAO,now)
            s.update(perfil_id='frozen-size-smoke',rng_state=random.Random(0).getstate(),
                     contexto_fuso=0,pausado=True)
            s['medidas_peixes']=sizes.empty_sizes(s['perfil_id'])
            e=FishingEngine(s);event=e.begin_strike(now,0)
            assert 'measurement' in event
            assert g._commit(e.advance(0,now,0))
            result={'pending':event,'coins':s['moedas_centavos']}
        elif mode=='deliver':
            previous=json.loads((output/'pending.json').read_text(encoding='utf-8'))['state']
            assert g.estado['pesca_pendente']==previous['pending']
            frozen=copy.deepcopy(g.estado['pesca_pendente'])
            g.estado['vara']=1;g.estado['barco']=1
            g.sortear();event=g._last_result
            assert event['measurement']==frozen['measurement']
            assert g.estado['moedas_centavos']==previous['coins']+frozen['gain_cents']
            sid=event['species_id'];s=copy.deepcopy(g.estado)
            s['museu']['aquario']=[sid,None,None];s['museu']['exemplares']=['menor','maior','maior']
            assert g._commit(s)
            assert s['medidas_peixes']['records'][sid]['n']==1
            assert 'med_primeira' in s['conquistas']
            g.capturando=.6;g.popup=[g._describe(event)[0],'#ffe3ac',4]
            g.grab().save(str(output/'exe-captura.png'))
            museum=MuseuDialog(g);museum.setAttribute(Qt.WA_DontShowOnScreen,True)
            museum.show();app.processEvents();museum.grab().save(str(output/'exe-museu.png'))
            assert sizes.fmt(event['measurement']['mm']) in museum.details[0].text()
            museum.accept();museum.deleteLater()
            result={k:copy.deepcopy(s[k]) for k in ('medidas_peixes','museu','conquistas','moedas_centavos','inventario_por_id')}
        elif mode=='reopen':
            previous=json.loads((output/'deliver.json').read_text(encoding='utf-8'))
            for key,value in previous['state'].items():assert g.estado[key]==value,key
            assert g.estado['pesca_pendente'] is None
            assert grant(g.estado,CATALOGO)==[]
            result={'identical_records_inventory_money_awards_museum':True}
        else:raise ValueError('Modo de smoke desconhecido.')
        assert g.salvar();g.close();app.processEvents();assert g._closed
        (output/(mode+'.json')).write_text(json.dumps({'ok':True,'frozen':bool(getattr(sys,'frozen',False)),
            'schema':g.estado['schema_version'],'state':result,'save':os.environ['PESCA_IDLE_SAVE_PATH']},ensure_ascii=False,indent=2),encoding='utf-8')
        return 0
    except Exception:
        (output/(mode+'-falha.txt')).write_text(traceback.format_exc(),encoding='utf-8')
        return 1
