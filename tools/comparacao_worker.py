"""Execute one immutable revision in a child process; synthetic profiles only."""
import argparse,copy,hashlib,json,os,random,sys,time,traceback,uuid,types
from datetime import datetime,timezone
from pathlib import Path

class TraceRandom(random.Random):
    draws=[]
    def random(self):
        value=super().random();self.draws.append(['random',value]);return value
    def getrandbits(self,k):
        value=super().getrandbits(k);self.draws.append(['getrandbits',k,value]);return value

def run(args):
    source=Path(args.source).resolve();output=Path(args.output).resolve()
    profile=source/'qa'/'comparador'/args.role
    profile.mkdir(parents=True,exist_ok=False)
    for name in ('tmp','appdata','localappdata'):(profile/name).mkdir()
    # Set the entire persistence boundary BEFORE any product import.
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(profile/'guard.json'),APPDATA=str(profile/'appdata'),
        LOCALAPPDATA=str(profile/'localappdata'),TEMP=str(profile/'tmp'),TMP=str(profile/'tmp'),
        QT_QPA_PLATFORM='offscreen',PESCA_IDLE_QA_DIR=str(profile/'outputs'))
    if not Path(os.environ['PESCA_IDLE_SAVE_PATH']).is_relative_to(source):raise RuntimeError('Profile outside source')
    clock=[1792281600.0];time.time=lambda:clock[0]
    uuid.uuid4=lambda:uuid.UUID(int=20261019)
    sys.dont_write_bytecode=True;sys.path.insert(0,str(source))
    import pesca_idle as game
    import pesca_save as save
    import pesca_pescaria as fishing
    import pesca_offline as offline
    import pesca_catalogo as catalog
    from pesca_loja import CATALOGO,CAT
    from pesca_conquistas import grant
    from pesca_moedas import can_buy
    import PySide6
    fishing.random=types.SimpleNamespace(Random=TraceRandom)  # Spy only the fishing stream, not tempfile/UUID randomness.
    for module in (game,save,fishing,offline,catalog):
        if not Path(module.__file__).resolve().is_relative_to(source):raise RuntimeError('Wrong imported revision')
    fixture=json.loads(Path(args.fixtures).read_text(encoding='utf-8'))
    midnight=datetime.fromisoformat(fixture['date_utc']).replace(tzinfo=timezone.utc).timestamp()
    def fresh(case,start):
        clock[0]=start
        s=save.migrate({},game.ESTADO_PADRAO,start)
        s.update(perfil_id='paired-'+str(case['seed']) if case['kind']=='historical' else 'synthetic-'+case['id'],
                 vara=case['level'],barco=case['level'],rng_state=random.Random(case['seed']).getstate(),
                 ultimo_processado_utc=start,contexto_fuso=fixture['offset_seconds'])
        if 'medidas_peixes' in s:
            from pesca_tamanhos import empty_sizes
            s['medidas_peixes']=empty_sizes(s['perfil_id'])
        catalog.desbloquear(s);TraceRandom.draws.clear();return s
    def frame(state,events=(),**extra):
        return copy.deepcopy({'state':state,'events':list(events),**extra})
    def award(state):return grant(state,CATALOGO)
    # Only presentation/scheduler adapters are stubbed; purchase/price/debit/upgrade/
    # commit methods below are the real JogoPesca/LojaDialog methods of each SHA.
    class Facade:
        custo_peca=game.JogoPesca.custo_peca
        pecas_necessarias=game.JogoPesca.pecas_necessarias
        comprar_peca=game.JogoPesca.comprar_peca
        _commit=game.JogoPesca._commit
        mostrar_popup=game.JogoPesca.mostrar_popup
        atualizar_tooltip=game.JogoPesca.atualizar_tooltip
        DURACAO_POPUP=game.JogoPesca.DURACAO_POPUP
        def __init__(self,state,store):
            self.estado=state;self._store=store;self._save_error=None;self.pausado=False
            self.popup=None;self._popup_queue=[]
        def tick(self):pass  # Instant action: clock already advanced through the real core.
        def setToolTip(self,text):self.tooltip=text
    class Shop:
        acao=game.LojaDialog.acao
        def __init__(self,g,id_):self.jogo=g;self.id_=id_
        def id_atual(self):return self.id_
        def slot_atual(self):return CAT[self.id_][1]
        def preencher(self):pass
        def atualizar_moedas(self):pass
    records=[];historical=[]
    for case in fixture['cases']:
        start=midnight+case['hour']*3600
        if case['kind']=='transition':start-=10
        if case['kind']=='pending':start=midnight+14*3600-.5
        s=fresh(case,start);timeline=[];kind=case['kind']
        if kind in ('historical','transition'):
            e=fishing.FishingEngine(s);e.advance(case['seconds'],start,0)
            timeline.append(frame(e.state,e.events))
            if kind=='historical':
                historical.append({'case':[case['seed'],case['hour'],case['level']],
                    'events':[{k:v for k,v in event.items() if k in ('id','species_id','context','gain_cents','categoria')} for event in e.events],
                    'coins':e.state['moedas_centavos'],'inventory':e.state['inventario_por_id'],
                    'phase':e.state['pesca'],'rng':hashlib.sha256(repr(e.rng.getstate()).encode()).hexdigest()})
        elif kind in ('offline','paused','expedition'):
            if kind=='paused':s['pausado']=True
            if kind=='expedition':
                offline.schedule(s,'enseada_do_poente',start+3600,3600,start)
                s,early=offline.replay(s,start+1800)
                timeline.append(frame(s,early['events'],report={k:v for k,v in early.items() if k!='events'},awards=award(s)))
            end=start+(case.get('seconds',14400) if kind!='expedition' else 10800)
            clock[0]=end;s,report=offline.replay(s,end)
            timeline.append(frame(s,report['events'],report={k:v for k,v in report.items() if k!='events'},awards=award(s)))
            before=copy.deepcopy(s);s,repeated=offline.replay(s,end)
            if s!=before or repeated['count']!=0:raise RuntimeError('Duplicate offline application')
            timeline.append(frame(s,repeated['events'],report={k:v for k,v in repeated.items() if k!='events'},awards=award(s)))
        elif kind=='pending':
            e=fishing.FishingEngine(s);pending=copy.deepcopy(e.begin_strike(start,0));s=e.advance(0,start,0)
            s['pausado']=True
            path=profile/(case['id']+'.json')
            with save.SaveStore(path) as store:store.save(s)
            with save.SaveStore(path) as store:s=store.load(game.ESTADO_PADRAO,start+30)
            if s['pesca_pendente']!=pending:raise RuntimeError('Pending changed across save/reopen')
            s,paused=offline.replay(s,start+30)
            timeline.append(frame(s,paused['events'],report={k:v for k,v in paused.items() if k!='events'}))
            s.update(vara=10,barco=10,pausado=False);catalog.desbloquear(s)
            if not fishing.travel(s,'rio_das_vitorias'):raise RuntimeError('Fixture travel failed')
            e=fishing.FishingEngine(s);s=e.advance(1.5,start+30,0)
            if len(e.events)!=1 or e.events[0]['gain_cents']!=pending['gain_cents']:raise RuntimeError('Frozen reward changed')
            timeline.append(frame(s,e.events,awards=award(s)))
            coins=s['moedas_centavos'];inventory=copy.deepcopy(s['inventario_por_id'])
            e=fishing.FishingEngine(s);e.state['pesca_pendente']=copy.deepcopy(pending)
            e.state['pesca']={'etapa':'fisgando','restante':1.5}
            e.finish_strike();s=e.advance(0,start+31.5,0)
            if e.events or s['moedas_centavos']!=coins or s['inventario_por_id']!=inventory:raise RuntimeError('Repeated confirmation paid twice')
            timeline.append(frame(s,e.events,awards=award(s)))
        elif kind=='migration':
            raw=copy.deepcopy(s);raw['schema_version']=3;raw.pop('pilot_kind',None);raw.pop('medidas_peixes',None)
            raw.update(moedas_centavos=123450,moedas=1234.5,vara=4,barco=3,total_pescados=500)
            raw['ultimo_salvo']=start
            raw['inventario_por_id']={'lambari':500};raw['legado_sem_contexto']={'lambari':500}
            raw['museu']['aquario']=['lambari',None,None]
            raw['cosmeticos'].append('chapeu_ninja');raw['equipados']['chapeu']='chapeu_ninja'
            catalog.desbloquear(raw)
            path=profile/(case['id']+'.json');payload=json.dumps(raw,ensure_ascii=False).encode();path.write_bytes(payload)
            with save.SaveStore(path) as store:s=store.load(game.ESTADO_PADRAO,start)
            backup=path.with_name(path.stem+'.pre-schema-3.json')
            artifacts=[]
            if backup.exists():
                if backup.read_bytes()!=payload:raise RuntimeError('Migration backup not exact')
                artifacts=[{'kind':'pre-schema-3-backup','exact_bytes':True}]
            elif path.read_bytes()!=payload:raise RuntimeError('Unmigrated original changed')
            if s.get('medidas_peixes',{}).get('records',{}):raise RuntimeError('Retroactive measurement')
            timeline.append(frame(s,additive_artifacts=artifacts))
            with save.SaveStore(path) as store:store.save(s)
            with save.SaveStore(path) as store:s=store.load(game.ESTADO_PADRAO,start)
            timeline.append(frame(s))
        elif kind=='progression':
            path=profile/(case['id']+'.json')
            with save.SaveStore(path) as store:
                facade=Facade(s,store)
                for elapsed in range(case['cadence'],case['seconds']+1,case['cadence']):
                    e=fishing.FishingEngine(facade.estado);s=e.advance(case['cadence'],start+elapsed-case['cadence'],0)
                    s['ultimo_processado_utc']=start+elapsed;clock[0]=start+elapsed;facade.estado=s
                    actions=[]
                    for tipo in ('vara','barco'):
                        price=facade.custo_peca(tipo)
                        if facade.estado[tipo]<case['purchase_target_level'] and can_buy(facade.estado,price):
                            before=facade.estado['moedas_centavos'];facade.comprar_peca(tipo)
                            if facade._save_error:raise RuntimeError('Purchase persistence error')
                            actions.append({'kind':'buy_part','type':tipo,'price':price,'before_cents':before,'after_cents':facade.estado['moedas_centavos']})
                    id_=case['cosmetic']
                    if id_ not in facade.estado['cosmeticos'] and can_buy(facade.estado,CAT[id_][3]):
                        before=facade.estado['moedas_centavos'];Shop(facade,id_).acao()
                        actions.append({'kind':'buy_cosmetic','id':id_,'price':CAT[id_][3],'before_cents':before,'after_cents':facade.estado['moedas_centavos']})
                    s=facade.estado
                    timeline.append(frame(s,e.events,awards=award(s),actions=actions))
                store.save(s)
            with save.SaveStore(path) as store:s=store.load(game.ESTADO_PADRAO,clock[0])
            timeline.append(frame(s,tag='reopened_after_progression'))
        else:raise ValueError('Unknown scenario kind: '+kind)
        records.append({'id':case['id'],'kind':kind,'complete':True,'timeline':timeline,
                        'rng_draws':copy.deepcopy(TraceRandom.draws)})
    from pesca_tempo import PERIODOS
    pools={f'{m}/{p}/{lv}':catalog.probabilities(m,p,lv) for m in catalog.LOCAIS for p,*_ in PERIODOS for lv in (0,3,10)}
    result={'format':1,'complete':True,'revision':args.revision,
        'fixture_sha256':hashlib.sha256(Path(args.fixtures).read_bytes()).hexdigest(),
        'schema':save.SCHEMA,'versions':{'python':sys.version.split()[0],'pyside6':PySide6.__version__},
        'catalogue':{'species':catalog.ESPECIES,'occurrences':catalog.OCORRENCIAS,'maps':catalog.LOCAIS,'shop':CATALOGO,
                     'pools':pools,'pool_order':{k:list(v) for k,v in pools.items()}},
        'scenarios':records,'historical_projection':historical}
    output.write_text(json.dumps(result,ensure_ascii=False,allow_nan=False),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--fixtures',required=True);ap.add_argument('--revision',required=True);ap.add_argument('--role',required=True)
    args=ap.parse_args()
    try:
        if not __debug__:raise RuntimeError('Optimized Python is not supported by this verification')
        run(args)
    except Exception:
        traceback.print_exc();sys.exit(2)
