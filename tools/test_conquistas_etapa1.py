"""Individual achievement, real-Qt action and persistence tests; synthetic only.

python -B tools/test_conquistas_etapa1.py --out qa/conquistas-run-01
Requires the existing Python/PySide6 environment. Never imports before isolation.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import sys
import time
import unittest
from unittest.mock import patch
import uuid

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    QA=args.out.resolve()
else:
    QA=ROOT/'qa'/('conquistas-'+uuid.uuid4().hex)
if not QA.is_relative_to(ROOT/'qa') or QA==ROOT/'qa':
    raise ValueError('Use um diretório novo dentro de qa deste candidato.')
QA.mkdir(parents=True,exist_ok=False)
for folder in ('profiles','appdata','localappdata','tmp'):
    (QA/folder).mkdir()
os.environ.update(PESCA_IDLE_SAVE_PATH=str(QA/'profiles'/'guard.json'),
                  APPDATA=str(QA/'appdata'),LOCALAPPDATA=str(QA/'localappdata'),
                  TEMP=str(QA/'tmp'),TMP=str(QA/'tmp'),QT_QPA_PLATFORM='offscreen',
                  PESCA_IDLE_MOBILE='0')
sys.path.insert(0,str(ROOT))

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import Qt,QEvent
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtTest import QTest
import pesca_idle as game
from pesca_ui import configure_app
from pesca_catalogo import ESPECIES,LOCAIS,LEGADO_49,EXPANSAO_88
from pesca_conquistas import definitions,grant,commit_with_achievements,fashionista_progress
from pesca_conquistas_etapa1 import CONFIG,GOALS,progress,FISH,SPECIAL,EPIC,BY_MAP,BY_CONTEXT
from pesca_loja import CATALOGO,CAT
from pesca_moedas import set_balance
from pesca_save import SaveStore,SaveError,migrate,validate_state,SCHEMA
from pesca_tamanhos import sample,rule_snapshot,exhibit
from pesca_museu_ui import MuseuDialog
from pesca_aquario_decor_ui import DecorationPanel
from pesca_aquario_decor import CAT as DECOR,CATALOGO as DECOR_LIST,empty_decoration
from pesca_pescaria import FishingEngine
from pesca_offline import replay

APP=QApplication.instance() or QApplication([])
APP.setQuitOnLastWindowClosed(False)
configure_app(APP)
NOW=1792771200
EXPECTED_CODES=('C01','C02','C03','C04','C05','C07','C09','C10','C11','C12','C13','C15',
                'C16','C17','C18','C19','C20','C21','C22','C23','C24','C25','C27','C28')
GOAL_BY_CODE={g['code']:g for g in GOALS}
FISH_IDS=sorted(FISH)
SPECIES_IDS=sorted(ESPECIES)
SPECIAL_IDS=sorted(SPECIAL)
MAP_IDS=CONFIG['map_ids']
PERIOD_IDS=CONFIG['period_ids']
PAID=CONFIG['sold_slots']
DECO_IDS=list(CONFIG['decorations'])
SLOTS=CONFIG['decoration_slots']
MEASURED=('lambari','tilapia_do_nilo','carpa_comum')
OBSERVED={}


def fresh():
    s=migrate({},game.ESTADO_PADRAO,NOW)
    s['perfil_id']='synthetic-achievements'
    s['rng_state']=random.Random(104729).getstate()
    s['medidas_peixes']['seed']='1'*64
    return s


def inventory(s,ids,n=1):
    s['inventario_por_id'].update({id_:n for id_ in ids})
    s['total_pescados']=sum(s['inventario_por_id'].values())


def regional(s,m,count=1):
    ids=sorted(BY_MAP[m]&FISH)[:count]
    s['registros_regionais'][m]={id_:1 for id_ in ids}


def temporal(s,period):
    m=next(m for m in MAP_IDS if BY_CONTEXT[m,period]&FISH)
    id_=sorted(BY_CONTEXT[m,period]&FISH)[0]
    s['registros_por_periodo'].setdefault(m,{})[period]={id_:1}


def decorated(s):
    s['museu']['decoracao']=empty_decoration()
    return s['museu']['decoracao']


def display(s,n=3):
    inventory(s,MEASURED,2)
    s['museu']['aquario']=list(MEASURED[:n])+[None]*(3-n)
    s['museu']['exemplares']=['maior']*3


def measured(s):
    display(s)
    data=s['medidas_peixes']
    for n,id_ in enumerate(MEASURED):
        r=rule_snapshot(id_)
        def record(u,index):
            item=sample(u,r)
            item.update(event_id=s['perfil_id']+':'+str(index),
                        utc=NOW,map_id='enseada_do_poente',periodo_id='dia')
            return item
        data['records'][id_]={'n':2,'menor':record(0,n*2+1),'maior':record(1,n*2+2)}
    data.update(quantity=6,last_counter=6,small_species=list(MEASURED),large_species=list(MEASURED))
    s['contador_eventos']=6


def cases(code):
    """Two independent synthetic profiles: just below/invalid, then satisfied."""
    low=fresh();high=None
    if code=='C01':
        inventory(low,[FISH_IDS[0]],24);high=copy.deepcopy(low);inventory(high,[FISH_IDS[0]],25)
    elif code in ('C02','C03'):
        n=10 if code=='C02' else 25
        inventory(low,SPECIES_IDS[:n-1]);high=copy.deepcopy(low);inventory(high,[SPECIES_IDS[n-1]])
    elif code in ('C04','C05'):
        n=5 if code=='C04' else 10
        inventory(low,SPECIES_IDS[:19],n);inventory(low,[SPECIES_IDS[19]],n-1)
        high=copy.deepcopy(low);inventory(high,[SPECIES_IDS[19]],n)
    elif code=='C07':
        inventory(low,[next(i for i in SPECIES_IDS if i not in EPIC)])
        high=copy.deepcopy(low);inventory(high,[sorted(EPIC)[0]])
    elif code=='C09':
        inventory(low,SPECIAL_IDS[:4]);high=copy.deepcopy(low);inventory(high,[SPECIAL_IDS[4]])
    elif code in ('C10','C11'):
        n=2 if code=='C10' else 8
        for m in MAP_IDS[:n-1]:regional(low,m)
        high=copy.deepcopy(low);regional(high,MAP_IDS[n-1])
    elif code in ('C12','C13'):
        n=3 if code=='C12' else 7
        for p in PERIOD_IDS[:n-1]:temporal(low,p)
        high=copy.deepcopy(low);temporal(high,PERIOD_IDS[n-1])
    elif code=='C15':
        for m in MAP_IDS[:2]:regional(low,m,3)
        regional(low,MAP_IDS[2],2);high=copy.deepcopy(low);regional(high,MAP_IDS[2],3)
    elif code=='C16':
        inventory(low,MEASURED,2);high=copy.deepcopy(low);display(high,1)
    elif code=='C17':
        display(low,2);high=copy.deepcopy(low);display(high,3)
    elif code=='C18':
        measured(low);high=copy.deepcopy(low);high['museu']['exemplares'][0]='menor'
    elif code=='C19':
        d=decorated(low);high=copy.deepcopy(low);high['museu']['decoracao']['compradas']=[DECO_IDS[0]]
    elif code=='C20':
        internal=[i for i in DECO_IDS if DECOR[i]['area']=='interna']
        external=next(i for i in DECO_IDS if DECOR[i]['area']=='externa')
        decorated(low)['compradas']=internal[:2];high=copy.deepcopy(low);high['museu']['decoracao']['compradas'].append(external)
    elif code=='C21':
        d=decorated(low)
        selected={slot:next(i for i in DECO_IDS if DECOR[i]['slot']==slot) for slot in SLOTS}
        d['compradas']=list(selected.values());d['equipadas']=dict(selected)
        d['equipadas'][SLOTS[-1]]=None
        high=copy.deepcopy(low);high['museu']['decoracao']['equipadas'][SLOTS[-1]]=selected[SLOTS[-1]]
    elif code=='C22':
        decorated(low)['compradas']=DECO_IDS[:-1];high=copy.deepcopy(low);high['museu']['decoracao']['compradas'].append(DECO_IDS[-1])
    elif code=='C23':
        ids=[next(i for i in PAID if PAID[i]==slot) for slot in ('chapeu','roupa','boia')]
        low['cosmeticos']+=ids[:2];high=copy.deepcopy(low);high['cosmeticos'].append(ids[-1])
    elif code=='C24':
        ids=[i for i in PAID if PAID[i] in ('chapeu','roupa','boia')]
        chosen=[next(i for i in ids if PAID[i]==slot) for slot in ('chapeu','roupa','boia')]
        chosen+=(i for i in ids if i not in chosen)
        low['cosmeticos']+=chosen[:10]
        high=copy.deepcopy(low);high['cosmeticos'].append(next(i for i in PAID if PAID[i]=='bandeira'))
    elif code=='C25':
        low['cosmeticos']+=['chapeu_ninja','roupa_ninja'];low['equipados']['chapeu']='chapeu_ninja'
        high=copy.deepcopy(low);high['equipados']['roupa']='roupa_ninja'
    elif code=='C27':
        high=copy.deepcopy(low);high['vara']=1
    elif code=='C28':
        low['vara']=3;low['barco']=2;high=copy.deepcopy(low);high['barco']=3
    else:raise ValueError(code)
    return low,high


def drain():
    APP.processEvents();APP.sendPostedEvents(None,QEvent.DeferredDelete)


class Individual(unittest.TestCase):
    pass


def individual_test(code):
    def run(self):
        low,high=cases(code);id_=GOAL_BY_CODE[code]['id'];title=GOAL_BY_CODE[code]['title']
        self.assertFalse(progress(low)[code][1])
        self.assertTrue(progress(high)[code][1])
        before=copy.deepcopy(high);global_rng=random.getstate()
        result=definitions(high,CATALOGO)
        self.assertEqual(high,before);self.assertEqual(random.getstate(),global_rng)
        self.assertEqual(len(result),38)
        self.assertTrue(next(x[3] for x in result if x[0]==id_))
        self.assertIn(GOAL_BY_CODE[code]['difficulty'],next(x[2] for x in result if x[0]==id_))
        self.assertIn('Progresso:',next(x[2] for x in result if x[0]==id_))
        self.assertNotIn(title,grant(low,CATALOGO))
        awards=grant(high,CATALOGO)
        self.assertIn(title,awards);self.assertIn(id_,high['conquistas'])
        self.assertNotIn(title,grant(high,CATALOGO));self.assertEqual(high['conquistas'].count(id_),1)
        for key in before:
            if key not in ('conquistas','cosmeticos'):self.assertEqual(high[key],before[key],key)
        self.assertEqual(high['cosmeticos'],before['cosmeticos'])
        # Every goal gets its own durable round trip and non-revocation check.
        with SaveStore(QA/'profiles'/(code+'.json')) as store:
            store.save(high);loaded=store.load(game.ESTADO_PADRAO,NOW)
            self.assertIn(id_,loaded['conquistas']);self.assertNotIn(title,grant(loaded,CATALOGO))
        revoked=copy.deepcopy(low);revoked['conquistas']=[id_]
        grant(revoked,CATALOGO);self.assertIn(id_,revoked['conquistas'])
        OBSERVED[code]=dict(title=title,negative=True,positive=True,idempotent=True,
                            persistence=True,no_revocation=True,no_economic_or_rng_change=True)
    return run


for code in EXPECTED_CODES:
    setattr(Individual,'test_'+code.lower(),individual_test(code))


class Contracts(unittest.TestCase):
    def test_exact_approved_scope(self):
        self.assertEqual(tuple(g['code'] for g in GOALS),EXPECTED_CODES)
        self.assertEqual(len({g['id'] for g in GOALS}),24)
        self.assertEqual(set(CONFIG['species']),set(ESPECIES))
        self.assertEqual(set(CONFIG['sold_slots']),{i for i,slot,name,price in CATALOGO if price>0})
        self.assertEqual(set(CONFIG['decorations']),set(DECOR))
        self.assertEqual(set(CONFIG['map_ids']),set(LOCAIS))
        self.assertEqual(len(definitions(fresh(),CATALOGO)),38)
        self.assertEqual({g['difficulty'] for g in GOALS},{'Fácil','Moderado','Difícil'})

    def test_unknown_ids_free_items_and_book_do_not_count(self):
        s=fresh();s['inventario_por_id']={'unknown':99999,'bota_velha':99999}
        s['cosmeticos']+=['enciclopedia_viva','future_paid']
        decorated(s)['compradas']=['future_decor']
        s['registros_regionais']={'future_map':{'lambari':100},MAP_IDS[0]:{'unknown':100}}
        s['registros_por_periodo']={MAP_IDS[0]:{'future_period':{'lambari':100}}}
        s['museu']['aquario']=['unknown',None,None]
        self.assertFalse(any(x[1] for x in progress(s).values()))

    def test_contextless_legacy_never_becomes_regional_or_temporal(self):
        s=fresh();inventory(s,SPECIES_IDS,10);s['legado_sem_contexto']=dict(s['inventario_por_id'])
        p=progress(s)
        for code in ('C10','C11','C12','C13','C15'):self.assertFalse(p[code][1])
        self.assertTrue(p['C05'][1])

    def test_count_and_category_boundaries(self):
        s=fresh();s['inventario_por_id']={FISH_IDS[0]:True,FISH_IDS[1]:-1,FISH_IDS[2]:0}
        self.assertFalse(progress(s)['C01'][1])
        s['cosmeticos']+=[i for i in PAID if PAID[i]=='chapeu'][:10]
        self.assertFalse(progress(s)['C23'][1]);self.assertFalse(progress(s)['C24'][1])
        ids=[next(i for i in PAID if PAID[i]==slot) for slot in ('chapeu','roupa','boia','bandeira')]
        ids += [i for i in PAID if i not in ids][:6]
        s['cosmeticos']=ids[:9];self.assertFalse(progress(s)['C24'][1])
        s['cosmeticos']=ids;self.assertTrue(progress(s)['C24'][1])
        s['vara']=0;s['barco']=1;self.assertTrue(progress(s)['C27'][1])

    def test_display_and_ownership_guard(self):
        _,s=cases('C18')
        s['museu']['aquario'][2]=None;self.assertFalse(progress(s)['C18'][1])
        _,s=cases('C21')
        s['museu']['decoracao']['compradas'].pop();self.assertFalse(progress(s)['C21'][1])
        _,s=cases('C25')
        s['cosmeticos'].remove('roupa_ninja');self.assertFalse(progress(s)['C25'][1])
        s=fresh();display(s);s['museu']['aquario'][2]=next(iter(SPECIAL));inventory(s,SPECIAL_IDS)
        self.assertFalse(progress(s)['C17'][1])

    def test_all_legacy_goals_preserved_and_book_reward(self):
        s=fresh();inventory(s,SPECIES_IDS,10)
        s['cosmeticos']+=[i for i in PAID];s['vara']=s['barco']=10
        measured(s)
        inventory(s,SPECIES_IDS,10)  # Measurement fixture creates two of each pilot fish.
        rows=definitions(s,CATALOGO)[:14]
        expected=['vestir_todos','criatura_digital','rei_pesca','colecao_expansao_88','mestre_vara',
                  'mestre_barco','rei_piratas','fashionista','enciclopedia_viva','med_primeira',
                  'med_diminuto','med_excepcional','med_div_pequenos','med_div_grandes']
        self.assertEqual([x[0] for x in rows],expected)
        self.assertTrue(all(x[3] for x in rows));self.assertEqual(len(LEGADO_49),49)
        self.assertEqual(len(EXPANSAO_88),88)
        self.assertEqual(fashionista_progress(s)['total'],84)
        money=s['moedas_centavos'];grant(s,CATALOGO)
        self.assertEqual(s['cosmeticos'].count('enciclopedia_viva'),1)
        self.assertEqual(s['moedas_centavos'],money)
        self.assertEqual(grant(s,CATALOGO),[])

    def test_legacy_save_backup_and_idempotent_recognition(self):
        s=fresh();inventory(s,SPECIES_IDS[:10],5)
        s['schema_version']=3;s.pop('pilot_kind');s.pop('medidas_peixes')
        s['conquistas']=['unknown_historical_award']
        path=QA/'profiles'/'legacy-v3.json'
        original=json.dumps(s,ensure_ascii=False).encode('utf-8');path.write_bytes(original)
        with SaveStore(path) as store:
            loaded=store.load(game.ESTADO_PADRAO,NOW)
            self.assertEqual(path.with_name('legacy-v3.pre-schema-3.json').read_bytes(),original)
            self.assertTrue(progress(loaded)['C02'][1])
            self.assertFalse(progress(loaded)['C10'][1])
            self.assertFalse(progress(loaded)['C12'][1])
            grant(loaded,CATALOGO);store.save(loaded)
            first=store.load(game.ESTADO_PADRAO,NOW)
            self.assertEqual(grant(first,CATALOGO),[])
            self.assertIn('unknown_historical_award',first['conquistas'])
            self.assertEqual(first['inventario_por_id'],s['inventario_por_id'])
            self.assertEqual(first['schema_version'],SCHEMA)

    def test_seeded_fishing_online_and_offline_preserved(self):
        a=fresh();b=copy.deepcopy(a)
        left_events=[];right_events=[]
        for step in range(20):
            l=FishingEngine(a);a=l.advance(120,NOW+step*120,0);left_events+=l.events
            r=FishingEngine(b);b=r.advance(120,NOW+step*120,0);right_events+=r.events
            grant(b,CATALOGO)
        self.assertEqual(left_events,right_events)
        for key in a:
            if key!='conquistas':self.assertEqual(a[key],b[key],key)
        s=fresh();s['ultimo_processado_utc']=NOW
        off,report=replay(s,NOW+14400)
        engine=FishingEngine(s);active=engine.advance(14400,NOW,s['contexto_fuso'])
        grant(active,CATALOGO);grant(off,CATALOGO)
        for key in ('inventario_por_id','rng_state','moedas_centavos','registros_regionais',
                    'registros_por_periodo','medidas_peixes','conquistas'):
            self.assertEqual(active[key],off[key],key)
        self.assertEqual(report['paid_seconds'],14400)
        self.assertTrue(progress(off)['C01'][1])
        self.assertFalse(progress(s)['C01'][1])

    def test_pending_is_not_credited_early(self):
        s=fresh();inventory(s,[FISH_IDS[0]],24)
        e=FishingEngine(s);e.begin_strike(NOW,0)
        grant(e.state,CATALOGO)
        self.assertNotIn('etapa1_c01',e.state['conquistas'])
        old=e.state['pesca_pendente']['id'];before=e.state['moedas_centavos']
        e.finish_strike();grant(e.state,CATALOGO)
        self.assertEqual(e.state['ultimo_evento_aplicado'],old)
        self.assertGreaterEqual(e.state['moedas_centavos'],before)


class RealActions(unittest.TestCase):
    def session(self,state=None):
        path=QA/'profiles'/('gui-'+uuid.uuid4().hex+'.json')
        initial=copy.deepcopy(state) if state else fresh()
        initial['pausado']=True;initial['ultimo_processado_utc']=NOW
        with SaveStore(path) as store:store.save(initial)
        game.SAVE_PATH=path
        g=game.JogoPesca(wall_clock=lambda:NOW,monotonic_clock=lambda:0)
        g.relogio.stop();g.timer_save.stop()
        self.addCleanup(lambda:g.close() if not g._closed else None)
        self.addCleanup(drain)
        return g

    def dialog(self,cls,g,*args,**kwargs):
        d=cls(g,*args,**kwargs)
        d.setAttribute(Qt.WA_DontShowOnScreen,True)
        d.show();drain()
        self.addCleanup(d.close)
        self.addCleanup(d.deleteLater)
        return d

    def assert_award(self,g,code):
        self.assertIn(GOAL_BY_CODE[code]['id'],g.estado['conquistas'])
        disk=json.loads(g._store.path.read_text(encoding='utf-8'))
        self.assertIn(GOAL_BY_CODE[code]['id'],disk['conquistas'])

    def select_deco(self,p,id_):
        index=next(i for i in range(p.list.count()) if p.list.item(i).data(Qt.UserRole)==id_)
        p.list.setCurrentRow(index);drain()

    def test_decoration_purchase_equipment_and_preview(self):
        s=fresh();set_balance(s,1000000);g=self.session(s)
        p=DecorationPanel(g,shop=True);self.addCleanup(p.deleteLater)
        before=copy.deepcopy(g.estado)
        self.select_deco(p,DECO_IDS[0])
        self.assertEqual(g.estado,before)
        for item in DECOR_LIST:
            self.select_deco(p,item['id']);QTest.mouseClick(p.action,Qt.LeftButton);drain()
        for code in ('C19','C20','C21','C22'):self.assert_award(g,code)
        self.assertEqual(g.estado['moedas_centavos'],before['moedas_centavos']-sum(i['price'] for i in DECOR_LIST)*100)
        old=copy.deepcopy(g.estado['conquistas']);p.restore()
        self.assertEqual(g.estado['conquistas'],old)
        self.assertTrue(all(x is None for x in g.estado['museu']['decoracao']['equipadas'].values()))

    def test_museum_selection_and_specimen_actions(self):
        s=fresh();measured(s);s['museu']['aquario']=[None]*3
        g=self.session(s);d=self.dialog(MuseuDialog,g)
        for slot,id_ in enumerate(MEASURED):d.apply(slot,id_)
        for code in ('C16','C17'):self.assert_award(g,code)
        self.assertNotIn('etapa1_c18',g.estado['conquistas'])
        d.specimen_selectors[0].setCurrentIndex(1);drain()
        self.assertEqual(exhibit(g.estado,0)['band'],'diminuto')
        self.assert_award(g,'C18')
        before=copy.deepcopy(g.estado['conquistas']);d.apply(0,None)
        self.assertEqual(g.estado['conquistas'],before)

    def test_ninja_shop_purchase_grants_after_equipping(self):
        s=fresh();set_balance(s,10000);g=self.session(s)
        d=self.dialog(game.LojaDialog,g)
        for slot,id_ in (('chapeu','chapeu_ninja'),('roupa','roupa_ninja')):
            d.categoria.setCurrentIndex(1+list(game.SLOTS).index(slot))
            rows=d.listas[slot]
            index=next(i for i in range(rows.count()) if rows.item(i).data(Qt.UserRole)==id_)
            rows.setCurrentRow(index);drain();QTest.mouseClick(d.btn,Qt.LeftButton);drain()
        self.assert_award(g,'C25')
        self.assertEqual(g.estado['moedas_centavos'],600000)
        self.assertEqual(g.estado['equipados']['roupa'],'roupa_ninja')

    def test_upgrade_buttons_and_level_boundaries(self):
        s=fresh();set_balance(s,10000);g=self.session(s)
        for kind in ('vara','barco'):
            for _ in range(9):g.comprar_peca(kind)
        self.assertEqual((g.estado['vara'],g.estado['barco']),(3,3))
        for code in ('C27','C28'):self.assert_award(g,code)
        self.assertEqual(g.estado['moedas_centavos'],1000000-98000)

    def test_failed_commit_has_no_grant_no_notification_and_retry_once(self):
        g=self.session();_,candidate=cases('C19')
        baseline=copy.deepcopy(g.estado);saved=g._store.path.read_bytes()
        with patch.object(g._store,'save',side_effect=SaveError('synthetic disk full')):
            self.assertFalse(commit_with_achievements(g,candidate))
        self.assertEqual(g.estado['conquistas'],baseline['conquistas'])
        self.assertEqual(g._store.path.read_bytes(),saved)
        messages=([g.popup] if g.popup else [])+g._popup_queue
        self.assertFalse(any('Lar, doce aquário' in m[0] for m in messages))
        # Rebuild from authoritative state after failure, as the real UI does.
        retry=copy.deepcopy(g.estado);retry['museu']['decoracao']=candidate['museu']['decoracao']
        self.assertTrue(commit_with_achievements(g,retry));self.assert_award(g,'C19')
        self.assertTrue(commit_with_achievements(g,copy.deepcopy(g.estado)))
        messages=([g.popup] if g.popup else [])+g._popup_queue
        self.assertEqual(sum('Lar, doce aquário' in m[0] for m in messages),1)

    def test_retroactive_open_and_all_notifications(self):
        _,s=cases('C05');g=self.session(s)
        for code in ('C01','C02','C04','C05'):self.assert_award(g,code)
        g.verificar_conquistas()
        self.assertEqual(len(g.estado['conquistas']),len(set(g.estado['conquistas'])))
        # Exercise a burst larger than the previous catch-queue bound.
        g.popup=None;g._popup_queue=[]
        for i in range(45):g.mostrar_popup('Conquista sintética '+str(i))
        for i in range(50):g.mostrar_popup('Captura sintética '+str(i))
        messages=([g.popup] if g.popup else [])+g._popup_queue
        self.assertEqual(sum('Conquista' in m[0] for m in messages),45)
        self.assertNotIn('perfil-piloto',str(g._store.path))

    def test_all_38_real_notifications_and_no_economic_reward(self):
        g=self.session();s=fresh();measured(s);inventory(s,SPECIES_IDS,10)
        s['museu']['exemplares'][0]='menor'
        s['cosmeticos']+=list(PAID);s['equipados'].update(chapeu='chapeu_ninja',roupa='roupa_ninja')
        s['vara']=s['barco']=10
        for m in MAP_IDS:regional(s,m,3)
        for p in PERIOD_IDS:temporal(s,p)
        d=decorated(s);d['compradas']=DECO_IDS[:]
        d['equipadas']={slot:next(i for i in DECO_IDS if DECOR[i]['slot']==slot) for slot in SLOTS}
        g.popup=None;g._popup_queue=[];before=s['moedas_centavos']
        self.assertTrue(commit_with_achievements(g,s))
        self.assertEqual(len(g.estado['conquistas']),38)
        messages=([g.popup] if g.popup else [])+g._popup_queue
        self.assertEqual(len(messages),38)
        self.assertEqual(len({m[0] for m in messages}),38)
        self.assertEqual(g.estado['moedas_centavos'],before)
        self.assertEqual(g.estado['cosmeticos'].count('enciclopedia_viva'),1)

    def test_real_startup_offline_grants_and_persists(self):
        s=fresh();inventory(s,[FISH_IDS[0]],24);s['ultimo_processado_utc']=NOW-600
        s['pausado']=False
        path=QA/'profiles'/'startup-offline.json'
        with SaveStore(path) as store:store.save(s)
        game.SAVE_PATH=path
        g=game.JogoPesca(wall_clock=lambda:NOW,monotonic_clock=lambda:0)
        g.relogio.stop();g.timer_save.stop()
        self.addCleanup(g.close)
        self.assertGreater(g._last_offline['count'],0)
        self.assert_award(g,'C01')
        before=copy.deepcopy(g.estado);g.simular_offline()
        self.assertEqual(g.estado['inventario_por_id'],before['inventario_por_id'])
        self.assertEqual(g.estado['conquistas'],before['conquistas'])

    def test_real_online_tick_grants_and_persists(self):
        s=fresh();inventory(s,[FISH_IDS[0]],24);s['pausado']=False
        path=QA/'profiles'/'online-tick.json'
        with SaveStore(path) as store:store.save(s)
        clock={'wall':float(NOW),'mono':0.}
        game.SAVE_PATH=path
        g=game.JogoPesca(wall_clock=lambda:clock['wall'],monotonic_clock=lambda:clock['mono'])
        g.relogio.stop();g.timer_save.stop();self.addCleanup(g.close)
        self.assertNotIn('etapa1_c01',g.estado['conquistas'])
        for _ in range(90):
            clock['wall']+=1;clock['mono']+=1;g.tick()
        self.assert_award(g,'C01')
        self.assertEqual(g.estado['conquistas'].count('etapa1_c01'),1)

    def test_dialog_scroll_and_compact_render(self):
        g=self.session()
        with patch.object(g,'caixa') as box:g.mostrar_conquistas()
        _,text=box.call_args.args
        from pesca_ui import InfoDialog
        for width,height in ((640,700),(320,568)):
            d=self.dialog(InfoDialog,g,'Conquistas',text)
            d.setMinimumSize(280,180);d.resize(width,height);drain()
            self.assertEqual(d.page.text().count('Progresso:'),24)
            self.assertGreater(d.scroll.verticalScrollBar().maximum(),0)
            self.assertEqual(d.scroll.horizontalScrollBar().maximum(),0)
            self.assertTrue(d.grab().save(str(QA/f'conquistas-{width}-topo.png')))
            d.scroll.verticalScrollBar().setValue(d.scroll.verticalScrollBar().maximum());drain()
            self.assertTrue(d.grab().save(str(QA/f'conquistas-{width}-rodape.png')))
            self.assertEqual(d.scroll.verticalScrollBar().value(),d.scroll.verticalScrollBar().maximum())

    def test_menu_lists_all_38_and_progress(self):
        g=self.session()
        with patch.object(g,'caixa') as box:
            g.mostrar_conquistas()
            title,text=box.call_args.args
        self.assertEqual(title,'Conquistas')
        for meta in GOALS:self.assertIn(meta['title'],text)
        self.assertEqual(text.count('Progresso:'),24)


class RecordingResult(unittest.TextTestResult):
    def startTest(self,test):
        super().startTest(test);self._started=time.perf_counter()
    def stopTest(self,test):
        OBSERVED.setdefault('tests',[]).append(dict(test=test.id().split('.')[-1],seconds=round(time.perf_counter()-self._started,5)))
        super().stopTest(test)


if __name__=='__main__':
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                             for cls in (Individual,Contracts,RealActions))
    result=unittest.TextTestRunner(verbosity=2,resultclass=RecordingResult).run(suite)
    report=dict(source_base=CONFIG['source_commit'],python=platform.python_version(),
                pyside6=PYSIDE_VERSION,tests=result.testsRun,failures=len(result.failures),
                errors=len(result.errors),individual=OBSERVED,passed=result.wasSuccessful(),
                limits='Qt offscreen e perfis sintéticos; não testa Android nativo, EXE ou sessão humana prolongada.',
                product_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in ROOT.glob('pesca*.py')})
    (QA/'resultado.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
