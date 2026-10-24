"""Real-engine weather contracts. Run through validate_climate.py isolation."""
import ast,copy,json,os,random,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if not os.environ.get('PESCA_IDLE_SAVE_PATH') or not Path(os.environ['PESCA_IDLE_SAVE_PATH']).resolve().is_relative_to(ROOT/'qa'):
    raise RuntimeError('Execute via tools/validate_climate.py com perfil sintético explícito.')
from pesca_clima import IDS,DATA,context,daily_id,factor,affinities,new_climate,validate_climate
from pesca_catalogo import ESPECIES,LOCAIS,probabilities,desbloquear
from pesca_pescaria import FishingEngine,travel
from pesca_offline import replay,schedule
from pesca_save import SaveStore,SaveError,migrate,validate_state,SCHEMA
tree=ast.parse((ROOT/'pesca_idle.py').read_text(encoding='utf-8'))
DEFAULTS=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ESTADO_PADRAO' for t in n.targets))
START=datetime(2026,10,23,22,tzinfo=timezone(timedelta(hours=-3))).timestamp()


def fresh(seed=11,now=START):
    state=migrate({},DEFAULTS,now);state['perfil_id']='climate-fixture-'+str(seed)
    from pesca_tamanhos import empty_sizes
    state['medidas_peixes']=empty_sizes(state['perfil_id']);state['clima']=new_climate(state['perfil_id'],now)
    state['rng_state']=random.Random(seed).getstate();state['contexto_fuso']=-10800
    return state


class ClimateContracts(unittest.TestCase):
    def test_scope_and_approved_factors(self):
        maps={m for g in DATA['groups'] for m in g['maps']}
        species={s for g in DATA['groups'] for s in g['species']}
        self.assertEqual(maps,set(LOCAIS));self.assertEqual(len(species),25)
        self.assertTrue(species<=ESPECIES.keys())
        for g in DATA['groups']:
            self.assertTrue(set(g['sources'])<=DATA['sources'].keys())
            self.assertTrue(set(g['factors'])<=set(IDS));self.assertTrue(set(g['factors'].values())<={80,90,110,120})
        self.assertEqual(factor('mar_das_auroras','salmao_rosa','ventania'),1.1)
        self.assertEqual(factor('mangue_das_raizes','tainha','ventania'),.9)
        self.assertEqual(factor('pier_da_brisa','vaquita','chuva'),1)

    def test_calendar_global_day_restart_rollback(self):
        s=fresh();before=copy.deepcopy(s);a=context(s,START,-10800)
        for m in LOCAIS:
            s['local_atual_id']=m
            self.assertEqual(context(s,START,-10800),a)
        self.assertEqual(context(s,START+3600,-10800)['id'],a['id'])
        restored=migrate(json.loads(json.dumps(before)),DEFAULTS,START+10000)
        self.assertEqual(context(restored,START,-10800),a)
        self.assertEqual(context(restored,START+3600,-10800)['id'],a['id'])

    def test_calendar_all_weather_and_distribution(self):
        counts={id_:0 for id_ in IDS};seed=fresh()['clima']['seed'];day=datetime(2000,1,1)
        for i in range(10000):counts[daily_id(seed,(day+timedelta(days=i)).date().isoformat())]+=1
        self.assertTrue(all(1700<n<2300 for n in counts.values()),counts)

    def test_midnight_leap_year_offsets(self):
        s=fresh();s['clima']['active_since_utc']=0
        for offset in (-43200,-10800,0,19800,50400):
            zone=timezone(timedelta(seconds=offset))
            for date in [(2026,12,31),(2028,2,28),(2028,2,29)]:
                before=datetime(*date,23,59,59,tzinfo=zone).timestamp();after=before+1
                a=context(s,before,offset);b=context(s,after,offset)
                self.assertEqual(a['proxima_utc'],after);self.assertNotEqual(a['data'],b['data'])
                self.assertEqual(b['id'],daily_id(s['clima']['seed'],b['data']))

    def test_light_rule_and_neutral_unknown_species(self):
        for p in ['amanhecer','manha','dia','meio_dia','tarde','anoitecer']:
            self.assertEqual(factor('fossa_das_lanternas','peixe_lanterna_de_muller','chuva',p),1.1)
            self.assertEqual(factor('fossa_das_lanternas','peixe_lanterna_de_muller','sol_forte',p),.9)
        self.assertEqual(factor('fossa_das_lanternas','peixe_lanterna_de_muller','chuva','noite'),1)
        for weather in IDS:
            self.assertEqual(factor('fossa_das_lanternas','peixe_ogro',weather,'dia'),1)

    def test_weather_queries_never_use_fishing_rng(self):
        s=fresh();rng=random.Random();rng.setstate(s['rng_state']);before=rng.getstate();state=copy.deepcopy(s)
        for id_ in IDS:
            affinities(id_);probabilities('enseada_do_poente','dia',10,id_);context(s,START,-10800)
        self.assertEqual(before,rng.getstate());self.assertEqual(state,s)

    def test_midnight_pending_travel_equipment_freeze(self):
        start=datetime(2026,10,23,23,59,59,tzinfo=timezone(timedelta(hours=-3))).timestamp()
        s=fresh(now=start);s['barco']=10;desbloquear(s)
        with patch('pesca_clima.daily_id',side_effect=lambda seed,day:'chuva' if day=='2026-10-23' else 'neve'):
            engine=FishingEngine(s);frozen=copy.deepcopy(engine.begin_strike(start,-10800))
            engine.state['vara']=10;engine.state['barco']=0
            self.assertTrue(travel(engine.state,'rio_das_vitorias'))
            saved=migrate(json.loads(json.dumps(engine.advance(0,start,-10800))),DEFAULTS,start+1)
            self.assertEqual(saved['pesca_pendente'],frozen)
            engine=FishingEngine(saved);engine.advance(1.5,start,-10800)
            self.assertEqual(engine.events[0]['context'],frozen['context'])
            self.assertEqual(engine.state['moedas_centavos'],frozen['gain_cents'])
            self.assertEqual(engine.state['local_atual_id'],'rio_das_vitorias')
            self.assertEqual(context(engine.state,start+2,-10800)['id'],'neve')
            self.assertEqual(len(engine.events),1)
            with self.assertRaises(ValueError):engine.finish_strike()

    def test_migrate_versions_idempotent_preserves_progress(self):
        for version in [1,2,3,4]:
            s=fresh();s['vara']=3;s['barco']=4;desbloquear(s)
            s['inventario_por_id']={'lambari':10};s['inventario']={'Lambari':10};s['total_pescados']=10
            s['conquistas']=['rei_pesca'];s['moedas_centavos']=12345;s['moedas']=123.45
            s['museu']['aquario']=['lambari',None,None]
            s['schema_version']=version;s.pop('clima')
            if version<4:s.pop('pilot_kind');s.pop('medidas_peixes')
            first=migrate(s,DEFAULTS,START);second=migrate(json.loads(json.dumps(first)),DEFAULTS,START+10)
            self.assertEqual(json.loads(json.dumps(first)),second);self.assertEqual(first['schema_version'],5)
            for key in ['moedas_centavos','vara','barco','inventario_por_id','cosmeticos','equipados','conquistas','museu']:
                self.assertEqual(first[key],s[key],(version,key))

    def test_legacy_pending_keeps_old_outcome(self):
        s=fresh();engine=FishingEngine(s);old=engine.begin_strike(START,-10800)
        raw=copy.deepcopy(engine.state);raw['schema_version']=4;raw.pop('clima');raw['pesca_pendente']['context'].pop('clima')
        expected=copy.deepcopy(raw['pesca_pendente']);rng=copy.deepcopy(raw['rng_state'])
        new=migrate(raw,DEFAULTS,START+100)
        pending=copy.deepcopy(new['pesca_pendente']);weather=pending['context'].pop('clima')
        self.assertEqual(pending,expected);self.assertEqual(weather['id'],'legado');self.assertEqual(new['rng_state'],rng)
        replayed=FishingEngine(new);replayed.advance(1.5,START+100,-10800)
        self.assertEqual(replayed.state['moedas_centavos'],old['gain_cents'])

    def test_legacy_offline_remains_neutral(self):
        s=fresh();s['schema_version']=4;s.pop('clima');before=START-14400;s['ultimo_processado_utc']=before
        migrated=migrate(s,DEFAULTS,START);result,report=replay(migrated,START)
        self.assertEqual(report['paid_seconds'],14400)
        self.assertTrue(all(e['context']['clima']['id']=='legado' for e in report['events']))
        self.assertEqual(context(result,START,-10800)['id'],daily_id(result['clima']['seed'],'2026-10-23'))

    def test_online_offline_exact_cross_midnight(self):
        s=fresh();s['vara']=s['barco']=10;desbloquear(s)
        with patch('pesca_clima.daily_id',side_effect=lambda seed,day:'chuva' if day=='2026-10-23' else 'neve'):
            active=FishingEngine(s);active.advance(14400,START,-10800)
            offline,report=replay(s,START+14400)
            for key in ['rng_state','inventario_por_id','medidas_peixes','moedas_centavos','pesca','pesca_pendente','contador_eventos']:
                self.assertEqual(active.state[key],offline[key],key)
            self.assertEqual(active.events,report['events'])
            self.assertEqual({e['context']['clima']['id'] for e in report['events']},{'chuva','neve'})
            again,empty=replay(offline,START+14400);self.assertEqual(empty['count'],0)
            self.assertEqual(again['moedas_centavos'],offline['moedas_centavos'])

    def test_offline_limit_pause_future_expedition_partial(self):
        s=fresh();out,report=replay(s,START+86400*3)
        self.assertEqual(report['paid_seconds'],14400);self.assertEqual(report['discarded'],86400*3-14400)
        s['pausado']=True;out,report=replay(s,START+14400);self.assertEqual(report['count'],0)
        s['pausado']=False;s['barco']=10;desbloquear(s)
        schedule(s,'mar_das_auroras',START+7200,14400,START)
        future,r=replay(s,START+3600);self.assertEqual(r['paid_seconds'],0);self.assertEqual(future['expedicao']['status'],'agendada')
        partial,r=replay(s,START+10800);self.assertEqual(r['paid_seconds'],3600)
        self.assertTrue(all(e['context']['map_id']=='mar_das_auroras' for e in r['events']))
        self.assertEqual(partial['expedicao']['status'],'consumida')

    def test_atomic_roundtrip_backup_and_reject_future(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'qa') as folder:
            p=Path(folder)/'save.json';s=fresh();raw=copy.deepcopy(s);raw['schema_version']=4;raw.pop('clima');raw.pop('moedas')
            original=json.dumps(raw).encode();p.write_bytes(original)
            store=SaveStore(p)
            try:
                migrated=store.load(DEFAULTS,START)
                self.assertEqual(p.with_name('save.pre-schema-4.json').read_bytes(),original)
                self.assertEqual(store.load(DEFAULTS,START+9999)['clima'],migrated['clima'])
                stable=p.read_bytes();invalid=copy.deepcopy(migrated);invalid['clima']['version']=999
                with self.assertRaises(SaveError):store.save(invalid)
                self.assertEqual(p.read_bytes(),stable)
                with patch('pesca_save.os.replace',side_effect=OSError('synthetic disk failure')):
                    with self.assertRaises(SaveError):store.save(migrated)
                self.assertEqual(p.read_bytes(),stable)
            finally:store.close()

    def test_invalid_climate_and_frozen_context_rejected(self):
        for key,value in [('version',99),('seed','bad'),('active_since_utc',float('nan')),('active_since_utc',1e300)]:
            s=fresh();s['clima'][key]=value
            with self.assertRaises(SaveError):migrate(s,DEFAULTS,START)
        s=fresh();e=FishingEngine(s);e.begin_strike(START,-10800)
        huge=copy.deepcopy(e.state);huge['pesca_pendente']['context']['utc']=1e300
        with self.assertRaises(SaveError):validate_state(huge)
        for field,value in [('id','furacao'),('version',999),('data','2020-01-01'),('proxima_utc',START)]:
            modified=copy.deepcopy(e.state);modified['pesca_pendente']['context']['clima'][field]=value
            with self.assertRaises(SaveError):validate_state(modified)
