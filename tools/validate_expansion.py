"""Deterministic contract matrix, synthetic profiles and real Qt renderer QA."""
import ast
import copy
from datetime import datetime,timedelta,timezone
import gc
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
CHECKS=[]


def memory_mb():
    if os.name!='nt':return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),
            *[(name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]]
    data=Counters();data.cb=ctypes.sizeof(data)
    current=ctypes.windll.kernel32.GetCurrentProcess;current.restype=wintypes.HANDLE
    query=ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not query(current(),ctypes.byref(data),data.cb):raise ctypes.WinError()
    return data.WorkingSetSize/1048576


def check(id_,condition):
    if not condition:raise AssertionError(id_)
    CHECKS.append(id_)


def run(profile,out):
    os.environ['PESCA_IDLE_SAVE_PATH']=str(profile/'gui.json');os.environ['APPDATA']=str(profile/'appdata')
    os.environ['LOCALAPPDATA']=str(profile/'localappdata');os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from pesca_catalogo import DATA,ESPECIES,LOCAIS,OCORRENCIAS,LEGADO_49,EXPANSAO_88,eligible,probabilities,desbloquear
    from pesca_tempo import PERIODOS,periodo,snapshot,proxima_mudanca
    from pesca_save import SaveStore,SaveError,migrate
    from pesca_moedas import set_balance,credit
    from pesca_pescaria import FishingEngine,travel
    from pesca_offline import replay,schedule,cancel,expire_active
    from pesca_conquistas import grant,RECOMPENSA_LIVRO
    tree=ast.parse((ROOT/'docs/design/pesca_idle_base_6b29b4a.py.txt').read_text(encoding='utf-8-sig'))
    literals={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('ESTADO_PADRAO','LOOT','CATALOGO')}
    defaults=literals['ESTADO_PADRAO'];base=datetime(2026,10,6,16,30,tzinfo=timezone.utc).timestamp()
    def fresh(seed=7,start=base):
        s=migrate({},defaults,start);s['perfil_id']='test-profile';s['contexto_fuso']=0
        return FishingEngine(s,random.Random(seed)).advance(0,start,0)
    check('CAT-01 totals',len(ESPECIES)==88 and len(LOCAIS)==8 and len(OCORRENCIAS)==90 and len(LEGADO_49)==49 and len(EXPANSAO_88)==88)
    proposal=json.loads((ROOT/'docs/design/pescaidle_expansao_catalogo.json').read_text(encoding='utf-8'))
    period_alias={'manhã':'manha','meio-dia':'meio_dia'}
    expected={(name,entry['nome'],cat):{period_alias.get(p,p) for p in entry['periodos']}
              for key,cat in (('catalogos_peixes','peixe'),('encontros_especiais','especial'))
              for name,entries in proposal[key].items() for entry in entries}
    actual={(LOCAIS[o['map_id']]['nome'],ESPECIES[o['species_id']]['nome'],ESPECIES[o['species_id']]['categoria']):set(o['periods']) for o in OCORRENCIAS}
    check('CAT-01 exact names, classification, occurrences and periods',actual==expected)
    for old in literals['LOOT']:
        if old['tipo']=='peixe':
            s=next(s for s in ESPECIES.values() if s['nome']==old['nome'])
            check('CAT-01 old price/bonus '+s['id'],s['valor']==old['valor'] and s['rod_bonus']==(old['valor']>=25))
    for m in LOCAIS:
        for p in [x[0] for x in PERIODOS]:
            check('CAT-02 '+m+'/'+p,len(eligible(m,p,'peixe'))>=3)
            for rod in range(11):
                pool=probabilities(m,p,rod);allowed={o['species_id'] for o in eligible(m,p)}|{'bota_velha'}
                check('BAL-01 sum and strictly forbidden '+m+p+str(rod),abs(sum(pool.values())-1)<1e-12 and set(pool)==allowed and all(v>0 for v in pool.values()))
    check('CAT-03 Pacu local-night distinction','pacu' in probabilities('rio_das_vitorias','noite',10) and 'pacu' not in probabilities('enseada_do_poente','noite',10))
    for name,p in (('piabanha','amanhecer'),('piraputanga','manha'),('piapara','tarde'),('jau','anoitecer'),('jundia','noite'),('peixe_borboleta','dia'),('cirurgiao_patela','meio_dia')):
        matching=[s for s in ESPECIES if s==name or s.startswith(name+'_')]
        check('CAT-04 exclusive '+name,len(matching)==1 and all(o['periods']==[p] for o in OCORRENCIAS if o['species_id']==matching[0]))
    check('CAT-05 fish/special/trash',sum(s['categoria']=='peixe' for s in ESPECIES.values())==68 and sum(s['categoria']=='especial' for s in ESPECIES.values())==20 and 'bota_velha' not in ESPECIES)
    day=datetime(2026,10,6)
    minutes=[periodo(day+timedelta(minutes=i)) for i in range(1440)]
    check('CLK-01 all civil minutes',[minutes.count(p) for p,_,_,_ in PERIODOS]==[120,120,120,180,180,180,540])
    for id_,_,hour,_ in PERIODOS:
        edge=day.replace(hour=hour)
        check('CLK-02 '+id_,periodo(edge)==id_ and periodo(edge+timedelta(microseconds=1))==id_ and periodo(edge-timedelta(microseconds=1))!=id_)
        check('CLK-02 next strictly future '+id_,proxima_mudanca(edge)>edge)
    check('CLK-02 midnight',periodo(day)==periodo(day+timedelta(days=1))=='noite')
    s=fresh();s['barco']=10;desbloquear(s)
    engine=FishingEngine(s);ctx_time=datetime(2026,10,6,6,59,59,500000,tzinfo=timezone.utc).timestamp()
    event=engine.begin_strike(ctx_time,0);original=copy.deepcopy(event)
    engine.state['vara']=10;engine.state['barco']=8
    travel(engine.state,'rio_das_vitorias');travel(engine.state,'recife_das_cores')
    check('EVT-01 frozen start and queue',engine.state['pesca_pendente']==original and event['context']['periodo_id']=='amanhecer' and event['context']['map_id']=='enseada_do_poente')
    midway=engine.advance(.75,ctx_time,0);saved=json.loads(json.dumps(midway));restored=FishingEngine(saved)
    end=restored.advance(.75,ctx_time+.75,0)
    check('EVT-02 applied once after reload',len(restored.events)==1 and restored.events[0]==original and end['local_atual_id']=='recife_das_cores' and end['pesca_pendente'] is None)
    reread=FishingEngine(json.loads(json.dumps(end)));reread.advance(0,ctx_time+1.5,0)
    check('EVT-02 no repeated result',len(reread.events)==0 and reread.state['moedas']==end['moedas'])
    blocked=fresh();old=copy.deepcopy(blocked);check('EVT-04 blocked read-only',not travel(blocked,'rio_das_vitorias') and blocked==old)
    for hour,minute in ((16,30),(23,30),(4,30)):
        start=datetime(2026,10,6,hour,minute,tzinfo=timezone.utc).timestamp();s=fresh(start=start)
        active=FishingEngine(s);expected_state=active.advance(14400,start,0)
        offline,report=replay(s,start+14400)
        check('OFF-05 active/offline exact '+str(hour),offline['inventario_por_id']==expected_state['inventario_por_id'] and offline['moedas']==expected_state['moedas'] and offline['rng_state']==expected_state['rng_state'] and report['events']==active.events)
        periods={e['context']['periodo_id'] for e in report['events']}
        check('OFF-01/02 historic periods '+str(hour),periods==({'tarde','anoitecer','noite'} if hour==16 else {'noite'} if hour==23 else {'noite','amanhecer','manha'}))
        for e in report['events']:
            check('OFF historic exact event pool',e['species_id'] in probabilities(e['context']['map_id'],e['context']['periodo_id'],e['context']['vara']))
    s=fresh();long,report=replay(s,base+40000);check('OFF-03 first four hours',report['paid_seconds']==14400 and report['discarded']==25600 and all(e['context']['utc']<=base+14400 for e in report['events']))
    twice,report2=replay(long,base+40000);check('OFF-03 reload no duplicate',report2['count']==0 and twice['moedas']==long['moedas'])
    for delta in (0,-100,.01,14400-1e-6,14400,14400+1e-6):
        outstate,r=replay(s,base+delta);check('OFF-04 limit/negative '+str(delta),0<=r['paid_seconds']<=14400 and outstate['ultimo_processado_utc']>=base and outstate['moedas']>=0)
    paused=fresh();paused['pausado']=True;after,r=replay(paused,base+1000)
    check('EVT-03 paused absence',after['inventario_por_id']==paused['inventario_por_id'] and after['pesca']==paused['pesca'] and r['count']==0)
    check('CLK-03 UTC/fixed offset',snapshot(base,0)['local_iso']!=snapshot(base,3600)['local_iso'])
    for return_hour,budget,status in ((4,0,'agendada'),(6,3600,'consumida'),(8,7200,'consumida')):
        start=datetime(2026,10,6,22,tzinfo=timezone.utc).timestamp();plan_start=start+7*3600
        s=fresh(start=start);s['barco']=10;desbloquear(s);schedule(s,'rio_das_vitorias',plan_start,7200,start)
        n=start+(return_hour+2)*3600;after,r=replay(s,n)
        check('EXP-01/02 return '+str(return_hour),r['paid_seconds']==budget and r['mode']=='expedicao' and after['expedicao']['status']==status)
        again,r2=replay(after,n);check('EXP-02 once '+str(return_hour),r2['count']==0 and again['moedas']==after['moedas'])
        if r['events']:check('EXP-01 scheduled historical map',all(e['context']['map_id']=='rio_das_vitorias' and plan_start<=e['context']['utc']<=plan_start+7200 for e in r['events']))
        if return_hour==4:
            cancel(after);no_retro,r3=replay(after,n);check('EXP-03 cancellation no retro',r3['count']==0)
        expire_active(s,plan_start);check('EXP-03 open-at-start expires',s['expedicao']['status']=='expirada')
    legacy=copy.deepcopy(defaults);legacy.update(moedas=1234.57,barco=6,vara=4,total_pescados=999,
        inventario={'Lambari':10,'Pacu':5,'Espécie antiga desconhecida':7},ultimo_salvo=base,
        conquistas=['rei_pesca'],campo_futuro={'preservado':True})
    legacy['cosmeticos'].append('chapeu_pikachu')
    path=profile/'migration.json';path.write_text(json.dumps(legacy),encoding='utf-8');original_bytes=path.read_bytes()
    store=SaveStore(path);migrated=store.load(defaults,base)
    check('SAV-01 exact legacy fields',all(migrated[k]==legacy[k] for k in ('moedas','barco','vara','total_pescados','conquistas','campo_futuro','equipados')))
    check('SAV-01 byte-exact backup',path.with_name('migration.pre-expansao-v1.json').read_bytes()==original_bytes)
    check('SAV-01 roundtrip idempotent',store.load(defaults,base)==migrated)
    check('SAV-02 unknown names recoverable',migrated['inventario_legado_desconhecido']=={'Espécie antiga desconhecida':7})
    check('ACH-02 no fabricated context',migrated['registros_regionais']=={} and migrated['registros_por_periodo']=={} and migrated['legado_sem_contexto']=={'lambari':10,'pacu':5})
    check('SAV-01 historic absence marker',migrated['ultimo_processado_utc']==base)
    check('SAV-02 distinct profiles',migrate({},defaults,base)['perfil_id']!=migrate({},defaults,base)['perfil_id'])
    broken=copy.deepcopy(migrated);broken['local_atual_id']='lost_map';fixed=migrate(broken,defaults,base)
    check('SAV-02 invalid map preserved diagnostic',fixed['local_atual_id']=='enseada_do_poente' and fixed['diagnosticos_migracao']['local_anterior_invalido']=='lost_map')
    try:SaveStore(path)
    except SaveError:check('SAV-05 exclusive writer',True)
    else:check('SAV-05 exclusive writer',False)
    before=path.read_bytes();candidate=copy.deepcopy(migrated);credit(candidate,10000)
    with patch('pesca_save.os.replace',side_effect=OSError('injected replace failure')):
        try:store.save(candidate)
        except SaveError:pass
        else:raise AssertionError('SAV-03 missing write error')
    check('SAV-03 original preserved on write failure',path.read_bytes()==before and store.last_good==migrated)
    with patch('pesca_save.os.fsync',side_effect=OSError('injected flush failure')):
        try:store.save(candidate)
        except SaveError:pass
        else:raise AssertionError('SAV-03 missing fsync error')
    check('SAV-04 before confirmation unchanged bytes/watermark',path.read_bytes()==before and store.last_good==migrated)
    durable,r=replay(migrated,base+100);store.save(durable);store.close()
    store=SaveStore(path);confirmed=store.load(defaults,base+100);once,r=replay(confirmed,base+100)
    check('SAV-04 after confirmation no replay',r['count']==0 and once['moedas']==durable['moedas']);store.close()
    for content in ('{bad json',json.dumps({'schema_version':999})):
        invalid=profile/'invalid.json';invalid.write_text(content,encoding='utf-8');lock=SaveStore(invalid)
        try:lock.load(defaults,base)
        except SaveError:check('SAV-03 invalid untouched',invalid.read_text(encoding='utf-8')==content)
        else:raise AssertionError('SAV-03 accepted invalid save')
        finally:lock.close()
    import pesca_idle as game
    historic=fresh();historic['inventario_por_id']={id_:1 for id_ in LEGADO_49};grant(historic,game.CATALOGO)
    check('ACH-01 fixed 49 incomplete 88','rei_pesca' in historic['conquistas'] and 'colecao_expansao_88' not in historic['conquistas'])
    grant(migrated,game.CATALOGO);check('ACH-01 keep prior unlocked','rei_pesca' in migrated['conquistas'])
    allstate=fresh();allstate['inventario_por_id']={id_:10 for id_ in ESPECIES};allstate['cosmeticos']=[id_ for id_,_,_,v in game.CATALOGO if v>0]
    first=grant(allstate,game.CATALOGO);second=grant(allstate,game.CATALOGO)
    check('Achievements reward without circular purchase','fashionista' in allstate['conquistas'] and 'enciclopedia_viva' in allstate['conquistas'] and allstate['cosmeticos'].count(RECOMPENSA_LIVRO)==1 and second==[] and allstate['equipados']['acessorio']!=RECOMPENSA_LIVRO)
    from PySide6.QtCore import Qt,QPoint,QSize
    from PySide6.QtGui import QImage,QPainter,QColor
    from PySide6.QtWidgets import QApplication
    from pesca_ui import configure_app
    from pesca_viagens_ui import ColecaoDialog,ViajarDialog,ExpedicaoDialog
    from pesca_especies_visual import species_image
    from pesca_visual import integer_viewport
    app=QApplication([]);configure_app(app);g=game.JogoPesca();g.relogio.stop();g.timer_save.stop()
    g.setAttribute(Qt.WA_DontShowOnScreen,True);g.show();out.mkdir(parents=True,exist_ok=True)
    before=copy.deepcopy(g.estado);disk=game.SAVE_PATH.read_bytes()
    for map_id in LOCAIS:
        for period_id,_,hour,_ in PERIODOS:
            g._preview_clock=datetime(2026,10,6,hour,30);g.fase=2
            img,_=g._render.render(g,map_id=map_id)
            check('ART-01 '+map_id+'/'+period_id,not img.isNull() and img.size()==QSize(256,144))
            img.scaled(768,432,Qt.IgnoreAspectRatio,Qt.FastTransformation).save(str(out/(map_id+'-'+period_id+'.png')))
            check('PERF-01 map cache max two',len(g._render.map_cache)<=2)
    check('EVT-05 56 previews read-only',g.estado==before and game.SAVE_PATH.read_bytes()==disk)
    check('ART species distinct identities',len({bytes(species_image(id_).constBits()) for id_ in ESPECIES})==88)
    # All hats/accessories in all locations with the shared actor anchors.
    gallery=QImage(8*512,2*288,QImage.Format_RGB32);gallery.fill(QColor('#172434'));p=QPainter(gallery)
    for i,(map_id,m) in enumerate(LOCAIS.items()):
        g._preview_clock=datetime(2026,10,6,12);g.previa={'chapeu':'chapeu_raposa','acessorio':'orbe_dragon','boneco':'boneco_capivara'}
        img,_=g._render.render(g,map_id=map_id);p.drawImage((i%4)*512,(i//4)*288,img.scaled(512,288,Qt.IgnoreAspectRatio,Qt.FastTransformation))
        for hat in g._render.hats:
            for accessory in [id_ for id_,slot,_,_ in game.CATALOGO if slot=='acessorio']:
                g.previa={'chapeu':hat,'acessorio':accessory};g.fase=15
                rendered,_=g._render.render(g,map_id=map_id)
                check('ART-02 cosmetics '+map_id+hat+accessory,not rendered.isNull())
    p.end();gallery.save(str(out/'mapas-galeria.png'));g.previa={};g._preview_clock=None
    for id_ in ('chapeu_raposa','chapeu_samurai'):
        g._render.character('roupa_vermelha',id_,0).scaled(256,448,Qt.IgnoreAspectRatio,Qt.FastTransformation).save(str(out/(id_+'.png')))
    g.estado['inventario_por_id']={'lambari':1,'pacu':5,'jundia':10}
    enc=ColecaoDialog(g);enc.setAttribute(Qt.WA_DontShowOnScreen,True);enc.show();app.processEvents()
    check('UI-01 only discovered by default',enc.lista.count()==3)
    for i in range(3):
        enc.lista.setCurrentRow(i);id_=enc.lista.currentItem().data(Qt.UserRole);n=g.estado['inventario_por_id'][id_]
        text=enc.detail.text();check('UI-01 1/5/10 '+id_,('Valor:' in text) and ((ESPECIES[id_]['raridade'] in text)==(n>=5)) and ((ESPECIES[id_]['curiosidade'] in text)==(n>=10)))
    enc.pistas.setChecked(True);check('UI-01 unknown hints',enc.lista.count()==88)
    enc.lista.setCurrentRow(8);id_=enc.lista.currentItem().data(Qt.UserRole);scroll=enc.lista.verticalScrollBar().value();enc.refresh()
    check('UI-01 selection/scroll survives refresh',enc.lista.currentItem().data(Qt.UserRole)==id_ and enc.lista.verticalScrollBar().value()==scroll)
    for i in range(enc.lista.count()):
        item=enc.lista.item(i);id_=item.data(Qt.UserRole)
        if id_ not in g.estado['inventario_por_id']:
            enc.lista.setCurrentRow(i);check('UI-01 unknown no name/science/value leak',ESPECIES[id_]['nome'] not in item.text() and ESPECIES[id_]['cientifico'] not in enc.detail.text() and 'Valor:' not in enc.detail.text())
            break
    enc.grab().save(str(out/'enciclopedia.png'));enc.accept();check('UI-01 timer stops',not enc.timer.isActive());enc.deleteLater()
    g.estado=before
    for cls,name in ((ViajarDialog,'viajar'),(ExpedicaoDialog,'expedicao')):
        dlg=cls(g);dlg.setAttribute(Qt.WA_DontShowOnScreen,True);dlg.show();app.processEvents();dlg.grab().save(str(out/(name+'.png')));dlg.accept();dlg.deleteLater()
    from PySide6.QtCore import QCoreApplication,QEvent,QTimer
    for i in range(20):
        for cls in (ColecaoDialog,ViajarDialog,ExpedicaoDialog):
            dlg=cls(g);dlg.accept();dlg.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
    check('PERF-01 dialogs no orphan timer',len(g.findChildren(QTimer))==2)
    # Preserve actual purchasing/preview coverage for every sold cosmetic.
    g._wall=lambda:base;g._monotonic=lambda:g.ultimo_tick
    shop=game.LojaDialog(g);set_balance(g.estado,10000000)
    for slot_index,slot in enumerate(game.SLOTS,1):
        shop.abas.setCurrentIndex(slot_index)
        prices=[game.CAT[shop.listas[slot].item(i).data(Qt.UserRole)][3] for i in range(shop.listas[slot].count())]
        check('UI-01 ascending store '+slot,prices==sorted(prices))
        for i in range(shop.listas[slot].count()):
            shop.listas[slot].setCurrentRow(i);id_=shop.id_atual()
            prior=copy.deepcopy(g.estado);check('EVT-05 cosmetic preview '+id_,g.previa.get(slot)==id_)
            shop.acao()
            if id_==RECOMPENSA_LIVRO:
                check('UI earned reward cannot be bought',id_ not in g.estado['cosmeticos']);continue
            expected=0 if id_ in prior['cosmeticos'] else game.CAT[id_][3]
            check('UI purchase/equip '+id_,g.estado['equipados'][slot]==id_ and g.estado['moedas']==prior['moedas']-expected)
            balance=g.estado['moedas'];shop.acao();check('UI owned no extra charge '+id_,g.estado['moedas']==balance)
    shop.accept();check('EVT-05 cosmetic preview clears',g.previa=={});shop.deleteLater()
    g.estado=before
    # Pixel evidence for each requested effect, daytime and nighttime.
    from pesca_efeitos import storm_window
    storm=next(t for t in range(31) if storm_window(t))
    accessories=['martelo_pesado','cajado_tempestade','teia_aracnidea','broche_lunar','orbe_dragon',
                 'sabre_energia','estrelas_orbitais','asas_fenix','asas_boreais','chama_yokai','enciclopedia_viva']
    effects=QImage(3*512,4*312,QImage.Format_RGB32);effects.fill(QColor('#172434'));ep=QPainter(effects)
    for i,id_ in enumerate(accessories):
        g.previa={'acessorio':id_};g.fase=storm+.3 if id_=='cajado_tempestade' else .3
        g._preview_clock=datetime(2026,10,6,12);img,_=g.desenhar_cena()
        ep.drawImage((i%3)*512,(i//3)*312,img.scaled(512,288,Qt.IgnoreAspectRatio,Qt.FastTransformation))
        ep.setPen(QColor('#ffe3ac'));ep.drawText((i%3)*512+12,(i//3)*312+307,game.CAT[id_][2])
        check('ART effect visible '+id_,not g._render.item_image('acessorio',id_).isNull())
    ep.end();effects.save(str(out/'efeitos.png'));g.previa={};g._preview_clock=None
    g._clock_snapshot=snapshot(g._wall());g.grab().save(str(out/'janela.png'))
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QMenu
    g.move(100,100)
    def mouse(kind,local,global_pos,button,buttons):
        app.sendEvent(g,QMouseEvent(kind,QPointF(*local),QPointF(*global_pos),button,buttons,Qt.NoModifier))
    mouse(QMouseEvent.MouseButtonPress,(30,50),(130,150),Qt.LeftButton,Qt.LeftButton)
    mouse(QMouseEvent.MouseMove,(30,50),(180,190),Qt.NoButton,Qt.LeftButton)
    mouse(QMouseEvent.MouseButtonRelease,(30,50),(180,190),Qt.LeftButton,Qt.NoButton)
    check('UI-02 actual window drag',g.pos()==QPoint(150,140) and not g._arrastando)
    g.posicionar();geo=app.primaryScreen().availableGeometry()
    check('UI-02 default position unchanged',g.x()==geo.right()+1-g.width() and g.y()==geo.bottom()+1-g.height())
    menu_items=[]
    def close_menu():
        for widget in app.topLevelWidgets():
            if isinstance(widget,QMenu):menu_items.extend(a.text() for a in widget.actions());widget.close()
    QTimer.singleShot(20,close_menu);g.abrir_menu()
    check('UI-01 all menu flows',all(x in menu_items for x in ('Loja','Enciclopédia','Conquistas','Viajar','Expedição offline','Sair')))
    for ratio in (1,1.25,1.5,1.75,2):
        rect,scale=integer_viewport(ratio);check('UI-02 whole physical pixels '+str(ratio),abs(rect.width()*ratio/256-scale)<1e-9)
    # Real pause, civil clock and suspension using injected clocks.
    clocks={'utc':base,'mono':10};g._wall=lambda:clocks['utc'];g._monotonic=lambda:clocks['mono']
    g.estado=fresh();g.ultimo_tick=10;g._ultimo_civil=base;g.pausado=True;g.estado['pausado']=True
    phase=copy.deepcopy(g.estado['pesca']);animation=g.fase;clocks.update(utc=base+100,mono=110);g.tick()
    check('EVT-03 pause visual keeps moving',g.estado['pesca']==phase and g.fase>animation and g._clock_snapshot['utc']==base+100)
    g.pausado=False;g.estado['pausado']=False;clocks.update(utc=base+200,mono=210);g.tick()
    suspend=copy.deepcopy(g.estado);again,r=replay(suspend,base+200)
    check('OFF-06 suspension once',r['count']==0 and g._last_offline['paid_seconds']==100)
    clocks.update(utc=base+150,mono=211);g.tick();check('CLK-03 backwards watermark',g.estado['ultimo_processado_utc']>=base+200)
    # Purchases and rewards use one durable snapshot; failed saves pause visibly.
    set_balance(g.estado,1000);g.comprar_peca('barco');g.comprar_peca('barco')
    check('UI purchases unlock maps',g.estado['barco']==1 and 'rio_das_vitorias' in g.estado['locais_desbloqueados'])
    before_fail=g._store.last_good
    with patch('pesca_save.os.replace',side_effect=OSError('injected GUI failure')):g.salvar()
    check('SAV-03 GUI visible error and safe pause',g.pausado and g._save_error and g.estado==before_fail)
    g._save_error=None;g.pausado=False;g._wall=time.time;g._monotonic=time.monotonic;g.ultimo_tick=time.monotonic();g._ultimo_civil=time.time()
    timings=[];latency=[];cache_counts=[];ram=[]
    for i in range(100):
        m=list(LOCAIS)[i%8];t=time.perf_counter();g._render.render(g,map_id=m);latency.append((time.perf_counter()-t)*1000)
        t=time.perf_counter()
        for _ in range(3):g._render.render(g,map_id=m)
        timings.append((time.perf_counter()-t)*1000/3);cache_counts.append(len(g._render.map_cache))
        if i%10==0:gc.collect();ram.append({'travel':i,'working_set_mb':memory_mb()})
    check('PERF-01 100 travels bounded caches',max(cache_counts)<=2 and len(g._render.cache)<=192)
    g.close();check('EVT close stops writers/timers',g._store.lock is None and not g.relogio.isActive() and not g.timer_save.isActive())
    report={'checks':len(CHECKS),'passed':CHECKS,'python':sys.version,'qt':game.sys.modules['PySide6'].__version__,
            'render_median_ms':statistics.median(timings),'render_p95_ms':sorted(timings)[94],
            'travel_median_ms':statistics.median(latency),'travel_p95_ms':sorted(latency)[94],
            'heavy_cache_max':max(cache_counts),'cosmetics_cache':len(g._render.cache),
            'ram_samples':ram,
            'gui':'Qt real widgets rendered offscreen; screenshots need explicit visual inspection; not interactive human play.'}
    (out/'validacao-expansao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='passed'},ensure_ascii=False))


if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='pesca-expansion-') as tmp:
        try:run(Path(tmp),Path(os.environ.get('PESCA_IDLE_QA_DIR',tmp)))
        finally:
            if 'PySide6.QtWidgets' in sys.modules:
                app=sys.modules['PySide6.QtWidgets'].QApplication.instance()
                if app:
                    for widget in app.topLevelWidgets():
                        if hasattr(widget,'_store'):widget._store.close()
