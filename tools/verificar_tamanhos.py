"""Focused size tests. All profiles live in this candidate, never in APPDATA."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'qa';TMP=QA/'tmp';TMP.mkdir(parents=True,exist_ok=True)
os.environ.update(PESCA_IDLE_SAVE_PATH=str(QA/'test-profile'/'save.json'),
                  APPDATA=str(QA/'appdata'),LOCALAPPDATA=str(QA/'localappdata'),
                  TEMP=str(TMP),TMP=str(TMP),QT_QPA_PLATFORM='offscreen')
sys.path.insert(0,str(ROOT))
import copy,json,math,random,tempfile,unittest,hashlib,time
from pesca_save import migrate,SaveStore,SaveError
from pesca_idle import ESTADO_PADRAO
from pesca_pescaria import FishingEngine
from pesca_offline import replay,schedule
from pesca_catalogo import ESPECIES
from pesca_conquistas import grant
from pesca_loja import CATALOGO
import pesca_tamanhos as sizes

NOW=1792332000

def fresh(seed=0):
    s=migrate({},ESTADO_PADRAO,NOW)
    s.update(perfil_id=f'size-qa-{seed}',rng_state=random.Random(seed).getstate(),
             ultimo_processado_utc=NOW,contexto_fuso=0)
    s['medidas_peixes']=sizes.empty_sizes(s['perfil_id'])
    return s

def add(s,id_,u):
    s['contador_eventos']+=1
    event={'id':s['perfil_id']+':'+str(s['contador_eventos']),'species_id':id_,
           'categoria':'peixe','gain':ESPECIES[id_]['valor'],'gain_cents':round(ESPECIES[id_]['valor']*100),
           'measurement':sizes.sample(u,sizes.rule_snapshot(id_)),
           'context':{'utc':NOW+s['contador_eventos'],'map_id':'enseada_do_poente','periodo_id':'dia'}}
    event['size_news']=sizes.apply(s,event)
    s['inventario_por_id'][id_]=s['inventario_por_id'].get(id_,0)+1;s['total_pescados']+=1
    return event

class SizeTests(unittest.TestCase):
    def test_01_distribution_borders_and_monotonicity(self):
        for id_ in sizes.RULES:
            r=sizes.rule_snapshot(id_)
            self.assertEqual(sizes.sample(0,r)['mm'],r['min_mm'])
            self.assertEqual(sizes.sample(1,r)['mm'],r['max_mm'])
            values=[sizes.sample(i/1000,r)['mm'] for i in range(1001)]
            self.assertEqual(values,sorted(values))
            self.assertLess(abs(sizes.cdf(r['small_cut_mm']+.5,r)-.05),.003)
            self.assertLess(abs(1-sizes.cdf(r['large_cut_mm']-.5,r)-.05),.003)
            scales=[sizes.visual_scale(mm,r) for mm in values]
            self.assertEqual(scales,sorted(scales))

    def test_02_separate_event_rng_repeatable(self):
        s=fresh(7);state=random.Random(7).getstate()
        event={'id':s['perfil_id']+':1','species_id':'lambari','categoria':'peixe'}
        a=copy.deepcopy(event);b=copy.deepcopy(event)
        sizes.attach(s,a);sizes.attach(s,b)
        self.assertEqual(a,b);self.assertEqual(s['rng_state'],state)
        saved=copy.deepcopy(a)
        old=copy.deepcopy(sizes.RULES['lambari'])
        try:
            sizes.RULES['lambari'].update(min_mm=20,typical_mm=50,max_mm=100)
            sizes.attach(s,a);self.assertEqual(a,saved)
        finally:sizes.RULES['lambari']=old
        other=copy.deepcopy(event);other['species_id']='pacu';sizes.attach(s,other)
        self.assertNotIn('measurement',other)

    def test_03_first_extremes_ties_and_idempotence(self):
        s=fresh();first=add(s,'lambari',.5)
        rec=s['medidas_peixes']['records']['lambari']
        self.assertEqual(rec['menor']['mm'],rec['maior']['mm'])
        before=copy.deepcopy(s['medidas_peixes']);self.assertEqual(sizes.apply(s,first),[])
        self.assertEqual(s['medidas_peixes'],before)
        tie=add(s,'lambari',.5);self.assertEqual(tie['size_news'],[])
        lo=add(s,'lambari',.02);hi=add(s,'lambari',.98)
        self.assertEqual(lo['size_news'],['menor']);self.assertEqual(hi['size_news'],['maior'])
        self.assertEqual(s['moedas_centavos'],0)

    def test_04_diversity_and_unique_achievements(self):
        s=fresh()
        for i in range(25):add(s,'lambari',.02)
        grant(s,CATALOGO);self.assertNotIn('med_div_pequenos',s['conquistas'])
        for id_ in ('tilapia_do_nilo','carpa_comum'):
            add(s,id_,.02);add(s,id_,.98)
        add(s,'lambari',.98)
        grant(s,CATALOGO);old=list(s['conquistas']);self.assertEqual(grant(s,CATALOGO),[])
        self.assertEqual(s['conquistas'],old)
        self.assertEqual(sum(x.startswith('med_') for x in old),5)
        self.assertEqual(len(s['medidas_peixes']['small_species']),3)
        self.assertEqual(s['moedas_centavos'],0)

    def test_05_pending_save_reopen_no_reroll_or_double_reward(self):
        e=FishingEngine(fresh(0))
        event=e.begin_strike(NOW,0)
        self.assertIn('measurement',event)
        e.advance(0,NOW,0)
        with tempfile.TemporaryDirectory(dir=TMP) as tmp:
            path=Path(tmp)/'save.json';store=SaveStore(path);store.save(e.state);store.close()
            store=SaveStore(path);s=store.load(ESTADO_PADRAO,NOW);store.close()
        self.assertEqual(s['pesca_pendente'],event)
        s['vara']=5;s['barco']=5
        resumed=FishingEngine(s);resumed.finish_strike()
        self.assertEqual(resumed.events[0]['measurement'],event['measurement'])
        self.assertEqual(resumed.state['moedas_centavos'],event['gain_cents'])
        before=copy.deepcopy(resumed.state['medidas_peixes']);coins=resumed.state['moedas_centavos']
        resumed.state['pesca_pendente']=copy.deepcopy(event);resumed.finish_strike()
        self.assertEqual(resumed.state['medidas_peixes'],before);self.assertEqual(resumed.state['moedas_centavos'],coins)

    def test_06_legacy_migration_no_retroactive_sizes(self):
        raw=fresh();raw['schema_version']=3;raw.pop('pilot_kind');raw.pop('medidas_peixes')
        raw['inventario_por_id']={'lambari':500};raw['museu']['aquario']=['lambari',None,None]
        raw['conquistas']=['rei_pesca'];raw['moedas_centavos']=12345;raw['moedas']=123.45
        raw.update(vara=4,barco=3,pecas_vara=2,pecas_barco=1,total_pescados=500)
        raw['cosmeticos'].append('chapeu_ninja');raw['equipados']['chapeu']='chapeu_ninja'
        raw['registros_regionais']={'enseada_do_poente':{'lambari':7}}
        raw['registros_por_periodo']={'enseada_do_poente':{'dia':{'lambari':7}}}
        raw['legado_sem_contexto']={'lambari':493}
        a=migrate(raw,ESTADO_PADRAO,NOW);b=migrate(a,ESTADO_PADRAO,NOW)
        self.assertEqual(a,b);self.assertEqual(a['medidas_peixes']['records'],{})
        self.assertEqual(a['museu'],raw['museu']);self.assertEqual(a['conquistas'],raw['conquistas'])
        self.assertEqual(a['moedas_centavos'],12345)
        for k in ('vara','barco','pecas_vara','pecas_barco','total_pescados','equipados','cosmeticos',
                  'inventario_por_id','legado_sem_contexto','registros_regionais','registros_por_periodo'):
            self.assertEqual(a[k],raw[k],k)
        with tempfile.TemporaryDirectory(dir=TMP) as tmp:
            p=Path(tmp)/'save.json';payload=json.dumps(raw).encode();p.write_bytes(payload)
            st=SaveStore(p);loaded=st.load(ESTADO_PADRAO,NOW);st.close()
            self.assertEqual(p.with_name('save.pre-schema-3.json').read_bytes(),payload)
            self.assertEqual(loaded['medidas_peixes']['quantity'],0)

    def test_07_invalid_data_preserves_last_good_file(self):
        s=fresh();add(s,'lambari',.5)
        with tempfile.TemporaryDirectory(dir=TMP) as tmp:
            p=Path(tmp)/'save.json';st=SaveStore(p);st.save(s);old=p.read_bytes()
            for value in (-1,True,999999):
                bad=copy.deepcopy(s);bad['medidas_peixes']['records']['lambari']['maior']['mm']=value
                with self.assertRaises(SaveError):st.save(bad)
                self.assertEqual(p.read_bytes(),old)
            bad=copy.deepcopy(s);bad['medidas_peixes']['version']=2
            with self.assertRaises(SaveError):st.save(bad)
            self.assertEqual(p.read_bytes(),old);st.close()
        with self.assertRaises(SaveError):SaveStore(ROOT.parent/'outside-refused.json')

    def test_08_future_parameters_keep_old_record_snapshot(self):
        s=fresh();add(s,'lambari',1);before=copy.deepcopy(s['medidas_peixes'])
        old=copy.deepcopy(sizes.RULES['lambari'])
        try:
            sizes.RULES['lambari'].update(min_mm=20,typical_mm=50,max_mm=100)
            again=migrate(s,ESTADO_PADRAO,NOW)
            self.assertEqual(again['medidas_peixes'],before)
        finally:sizes.RULES['lambari']=old

    def test_12_missing_or_corrupt_pilot_fields_are_not_silently_reset(self):
        s=fresh();add(s,'lambari',.5)
        variants=[]
        for value in (None,[],{'version':1}):
            v=copy.deepcopy(s);v['medidas_peixes']=value;variants.append(v)
        v=copy.deepcopy(s);v.pop('medidas_peixes');variants.append(v)
        v=copy.deepcopy(s);v['pilot_kind']='fluxo-proposal';variants.append(v)
        for v in variants:
            with self.assertRaises(SaveError):migrate(v,ESTADO_PADRAO,NOW)

    def test_09_offline_all_events_cap_and_no_repeat(self):
        for seed in range(4):
            s=fresh(seed);s.update(vara=3,barco=3)
            e=FishingEngine(s);online=e.advance(14400,NOW,0)
            offline,report=replay(s,NOW+14400)
            for k in ('inventario_por_id','moedas_centavos','rng_state','medidas_peixes','pesca_pendente'):
                self.assertEqual(online[k],offline[k])
            self.assertEqual(grant(online,CATALOGO),grant(offline,CATALOGO))
            self.assertEqual(online['conquistas'],offline['conquistas'])
            self.assertEqual(offline['medidas_peixes']['quantity'],sum('measurement' in x for x in report['events']))
            eight,r8=replay(s,NOW+28800)
            self.assertEqual(eight['medidas_peixes'],offline['medidas_peixes']);self.assertEqual(r8['paid_seconds'],14400)
            again,r=replay(eight,NOW+28800)
            self.assertEqual(again,eight);self.assertEqual(r['count'],0)
            self.assertEqual(sizes.offline_summary(report['events']).count('Medidas:'),1)

    def test_10_legacy_pending_stays_unmeasured(self):
        e=FishingEngine(fresh(0));event=e.begin_strike(NOW,0);event.pop('measurement')
        e.finish_strike();self.assertEqual(e.state['medidas_peixes']['quantity'],0)
        self.assertEqual(e.state['inventario_por_id'][event['species_id']],1)

    def test_11_pause_and_scheduled_offline(self):
        s=fresh(3);s['pausado']=True
        a,r=replay(s,NOW+1000);self.assertEqual(a['medidas_peixes']['quantity'],0)
        s['pausado']=False;schedule(s,'enseada_do_poente',NOW+3600,3600,NOW)
        a,r=replay(s,NOW+7200);self.assertEqual(r['paid_seconds'],3600)
        self.assertEqual(a['medidas_peixes']['quantity'],sum('measurement' in x for x in r['events']))
        a2,r2=replay(a,NOW+7200);self.assertEqual(a2['medidas_peixes'],a['medidas_peixes'])

def measure():
    distribution={}
    for sid in sizes.RULES:
        r=sizes.rule_snapshot(sid);rng=random.Random(20261018);n=100000
        small=large=0
        for _ in range(n):
            m=sizes.sample(rng.random(),r);small+=m['band']=='diminuto';large+=m['band']=='excepcional'
        distribution[sid]={'rule':r,'samples':n,'small':small,'large':large,
                           'small_probability_exact':sizes.cdf(r['small_cut_mm']+.5,r),
                           'large_probability_exact':1-sizes.cdf(r['large_cut_mm']-.5,r)}
    efforts=[]
    for seed in range(32):
        for hour in (7,20):
            start=NOW-NOW%86400+hour*3600;s=fresh(seed);s['ultimo_processado_utc']=start
            e=FishingEngine(s);elapsed=0.;milestones={};measured=0
            while elapsed<14400-1e-8:
                step=min(e.state['pesca']['restante'],14400-elapsed)
                e.advance(step,start+elapsed,0);elapsed+=step
                measured=e.state['medidas_peixes']['quantity']
                for id_,_,_,ok in sizes.definitions(e.state):
                    if ok:milestones.setdefault(id_,{'seconds':elapsed,'measured_catches':measured})
                e.events.clear()
            efforts.append({'seed':seed,'start_hour':hour,'horizon_seconds':14400,
                            'milestones':milestones,'measured_catches':measured})
    (QA/'distribuicao-esforco.json').write_text(json.dumps({'distribution':distribution,'effort':efforts,
        'scope':'32 paired seeds, starts 07/20h, level0 fixed, Enseada, 4h; not retention/global economy'},indent=2),encoding='utf-8')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SizeTests))
    (QA/'testes-nucleo.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}),encoding='utf-8')
    if not result.wasSuccessful():raise SystemExit(1)
    measure()
