"""Recover historical comparison and extend it using real, isolated revisions.

Exit: 0 equivalent; 1 divergence; 2 execution/configuration/incomplete run.
No product module is imported by this controller.
"""
import argparse,copy,hashlib,io,json,os,platform,re,subprocess,sys,zipfile,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'tools/fixtures/comparacao_tamanhos.json'
REFERENCE=ROOT/'docs/piloto-tamanhos/comparador/referencia-historica.json'
BASE='2a0353ff7c1cae2dca69d08c222b0660770d4385'
SIZE_IDS={'med_primeira','med_diminuto','med_excepcional','med_div_pequenos','med_div_grandes'}
SIZE_TITLES={'Uma fita, muitas histórias','Pequeno notável','Grande encontro','Pequena coleção','Grandes lembranças'}

def digest(data):return hashlib.sha256(data).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def invalid_constant(value):raise ValueError('Non-finite JSON constant: '+value)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'),parse_constant=invalid_constant)

def first_difference(a,b,path='$'):
    if type(a) is not type(b):return {'path':path,'left':a,'right':b,'reason':'type'}
    if isinstance(a,dict):
        if a.keys()!=b.keys():return {'path':path,'left_keys':list(a),'right_keys':list(b),'reason':'keys'}
        for key in a:
            diff=first_difference(a[key],b[key],path+'.'+key)
            if diff:return diff
    elif isinstance(a,list):
        if len(a)!=len(b):return {'path':path,'left_count':len(a),'right_count':len(b),'reason':'length'}
        for index,(x,y) in enumerate(zip(a,b)):
            diff=first_difference(x,y,f'{path}[{index}]')
            if diff:return diff
    elif a!=b:return {'path':path,'left':a,'right':b,'reason':'value'}
    return None

def measurement_known(m,record=False):
    keys={'mm','band','rule'}|({'event_id','utc','map_id','periodo_id'} if record else set())
    return (isinstance(m,dict) and set(m)==keys and type(m['mm']) is int and m['mm']>0
        and m['band'] in ('diminuto','habitual','excepcional') and isinstance(m['rule'],dict)
        and set(m['rule'])=={'version','min_mm','typical_mm','max_mm','small_cut_mm','large_cut_mm'})

def normalize_event(event,stats,pending=False):
    e=copy.deepcopy(event)
    if 'measurement' in e and measurement_known(e['measurement']):
        stats['pending_measurement_observations' if pending else 'measured_events']+=1
        e.pop('measurement')
    if 'size_news' in e and isinstance(e['size_news'],list) and set(e['size_news'])<={'primeira','menor','maior'}:
        stats['size_news_annotations']+=1;stats['record_flags']+=len(e.pop('size_news'))
    return e

def normalize_state(state,stats):
    s=copy.deepcopy(state)
    if s.get('schema_version')==4 and s.get('pilot_kind')=='tamanhos-v1':
        stats['schema4_observations']+=1;s['schema_version']=3;s.pop('pilot_kind')
    if 'medidas_peixes' in s:
        m=s['medidas_peixes']
        valid=isinstance(m,dict) and set(m)=={'version','seed','quantity','last_counter','records','small_species','large_species'}
        valid=valid and m['version']==1 and isinstance(m['records'],dict)
        valid=valid and type(m['version']) is int and type(m['quantity']) is int and m['quantity']>=0
        valid=valid and type(m['last_counter']) is int and m['last_counter']>=0 and isinstance(m['seed'],str) and bool(re.fullmatch('[0-9a-f]{64}',m['seed']))
        if valid:
            valid=all(isinstance(r,dict) and set(r)=={'n','menor','maior'} and type(r['n']) is int
                      and measurement_known(r['menor'],True) and measurement_known(r['maior'],True) for r in m['records'].values())
        if valid:
            valid=sum(r['n'] for r in m['records'].values())==m['quantity'] and all(
                isinstance(m[k],list) and len(set(m[k]))==len(m[k]) and all(x in m['records'] for x in m[k])
                for k in ('small_species','large_species'))
        if valid:
            stats['size_state_observations']+=1;stats['final_size_quantity']=m['quantity']
            stats['final_size_species']=sorted(m['records']);s.pop('medidas_peixes')
    if s.get('pesca_pendente') is not None:s['pesca_pendente']=normalize_event(s['pesca_pendente'],stats,True)
    if 'conquistas' in s:
        additive=[x for x in s['conquistas'] if x in SIZE_IDS]
        stats['size_achievement_ids']=sorted(set(stats['size_achievement_ids'])|set(additive))
        s['conquistas']=[x for x in s['conquistas'] if x not in SIZE_IDS]
    if isinstance(s.get('museu'),dict) and 'exemplares' in s['museu']:
        choices=s['museu']['exemplares']
        if isinstance(choices,list) and len(choices)==3 and set(choices)<={'menor','maior'}:
            stats['museum_choice_observations']+=1;s['museu'].pop('exemplares')
    return s

def stats_empty():
    return dict(measured_events=0,pending_measurement_observations=0,size_news_annotations=0,record_flags=0,
                schema4_observations=0,size_state_observations=0,final_size_quantity=0,final_size_species=[],
                size_achievement_ids=[],size_award_notifications=0,museum_choice_observations=0,migration_backups=0)

def normalize_scenario(scenario):
    result=copy.deepcopy(scenario);stats=stats_empty()
    for frame in result['timeline']:
        frame['state']=normalize_state(frame['state'],stats)
        frame['events']=[normalize_event(e,stats) for e in frame['events']]
        if 'awards' in frame:
            stats['size_award_notifications']+=sum(x in SIZE_TITLES for x in frame['awards'])
            frame['awards']=[x for x in frame['awards'] if x not in SIZE_TITLES]
        if 'additive_artifacts' in frame:
            artifacts=frame['additive_artifacts']
            if artifacts in ([],[{'kind':'pre-schema-3-backup','exact_bytes':True}]):
                stats['migration_backups']+=len(artifacts);frame.pop('additive_artifacts')
    return result,stats

def validate_run(run,fixture,fixture_sha):
    if fixture.get('version')!=1 or not isinstance(fixture.get('cases'),list) or not fixture['cases']:
        raise ValueError('Empty/unsupported scenario matrix')
    if run.get('format')!=1 or run.get('complete') is not True:raise ValueError('Incomplete/unsupported run')
    expected=[c['id'] for c in fixture['cases']]
    if len(set(expected))!=len(expected):raise ValueError('Duplicate fixture IDs')
    if run.get('fixture_sha256')!=fixture_sha:raise ValueError('Fixture hash mismatch')
    if [c.get('id') for c in run.get('scenarios',[])]!=expected:raise ValueError('Missing/reordered scenario results')
    for c,spec in zip(run['scenarios'],fixture['cases']):
        if c.get('complete') is not True or not c.get('timeline'):raise ValueError('Incomplete scenario: '+c['id'])
        counts={'historical':1,'transition':1,'offline':2,'paused':2,'expedition':3,'pending':3,'migration':2}
        expected_frames=(spec['seconds']//spec['cadence']+1) if spec['kind']=='progression' else counts[spec['kind']]
        if c.get('kind')!=spec['kind'] or len(c['timeline'])!=expected_frames:raise ValueError('Incomplete/wrong timeline: '+c['id'])
        for f in c['timeline']:
            if not isinstance(f.get('state'),dict) or not isinstance(f.get('events'),list):raise ValueError('Incomplete checkpoint')
            if not {'schema_version','perfil_id','moedas_centavos','inventario_por_id','rng_state','pesca','pesca_pendente','conquistas'}<=set(f['state']):raise ValueError('Incomplete state')
            if any(not {'id','species_id','context','gain','gain_cents','categoria'}<=set(e) for e in f['events']):raise ValueError('Incomplete capture event')
    historical_count=sum(c['kind']=='historical' for c in fixture['cases'])
    if len(run.get('historical_projection',[]))!=historical_count:raise ValueError('Incomplete historical projection')

def compare_runs(left,right,fixture,fixture_sha):
    validate_run(left,fixture,fixture_sha);validate_run(right,fixture,fixture_sha)
    if left['versions']!=right['versions']:raise ValueError('Different runtime/dependency versions')
    rows=[];first=first_difference(left['catalogue'],right['catalogue'],'$.catalogue')
    if first is None:first=first_difference(left['historical_projection'],right['historical_projection'],'$.historical_projection')
    for a,b in zip(left['scenarios'],right['scenarios']):
        x,sa=normalize_scenario(a);y,sb=normalize_scenario(b)
        diff=first_difference(x,y,'$.scenarios.'+a['id'])
        row={'id':a['id'],'kind':a['kind'],'equivalent':diff is None,'first_difference':diff,
             'base_events':sum(len(f['events']) for f in a['timeline']),
             'candidate_events':sum(len(f['events']) for f in b['timeline']),
             'rng_random_calls':sum(d[0]=='random' for d in b['rng_draws']),
             'rng_getrandbits_calls':sum(d[0]=='getrandbits' for d in b['rng_draws']),
             'base_rng_sha256':digest(json.dumps(a['rng_draws'],separators=(',',':')).encode()),
             'candidate_rng_sha256':digest(json.dumps(b['rng_draws'],separators=(',',':')).encode()),
             'base_normalized_sha256':digest(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()),
             'candidate_normalized_sha256':digest(json.dumps(y,sort_keys=True,ensure_ascii=False).encode()),
             'base_additions':sa,'candidate_additions':sb}
        rows.append(row)
        if first is None and diff:first=diff
    return {'equivalent':first is None,'first_difference':first,'scenarios':rows}

def export_revision(git,revision,destination):
    if not re.fullmatch('[0-9a-f]{40}',revision):raise ValueError('Use a full immutable SHA, not a branch/ref')
    resolved=subprocess.check_output([git,'-C',str(ROOT),'rev-parse',revision+'^{commit}'],stderr=subprocess.PIPE).decode().strip()
    if resolved!=revision:raise ValueError('Commit does not resolve exactly')
    names=subprocess.check_output([git,'-C',str(ROOT),'ls-tree','-r','--name-only','-z',revision]).decode().split('\0')
    names=[n for n in names if (len(Path(n).parts)==1 and n.endswith('.py')) or
           (n.startswith('assets/') and '/source/' not in n and n.endswith(('.png','.json')))]
    payload=subprocess.check_output([git,'-C',str(ROOT),'archive','--format=zip',revision,'--',*names])
    destination.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for item in z.infolist():
            target=(destination/item.filename).resolve()
            if not target.is_relative_to(destination.resolve()):raise ValueError('Unsafe archive member')
        z.extractall(destination)
    return {n:digest((destination/n).read_bytes()) for n in names}

def execute_worker(git,revision,role,work,fixtures,timeout):
    started=time.perf_counter()
    source=work/role/'source';manifest=export_revision(git,revision,source)
    record=work/(role+'.json');log=work/(role+'.log')
    env=dict(os.environ,PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
    for key in ('PYTHONPATH','PYTHONOPTIMIZE','PESCA_IDLE_SAVE_PATH','PESCA_IDLE_MOBILE','PESCA_IDLE_CONSOLE'):
        env.pop(key,None)
    command=[sys.executable,'-X','utf8','-B',str(ROOT/'tools/comparacao_worker.py'),
        '--source',str(source),'--output',str(record),'--fixtures',str(fixtures),
        '--revision',revision,'--role',role]
    with log.open('wb') as f:
        proc=subprocess.run(command,cwd=source,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    if proc.returncode!=0 or not record.exists():raise RuntimeError('Worker '+role+' failed/incomplete; inspect '+str(log))
    if any(digest((source/n).read_bytes())!=sha for n,sha in manifest.items()):raise RuntimeError('Product source/assets changed in worker')
    dump(work/(role+'-source-manifest.json'),{'revision':revision,'files':manifest,'unchanged_after_execution':True})
    dump(work/(role+'-execution.json'),{'revision':revision,'role':role,'exit_code':proc.returncode,
         'elapsed_seconds':time.perf_counter()-started,'exported_files':len(manifest),'unchanged_after_execution':True})
    return read(record)

def historical_status(run,reference):
    rows=run['historical_projection']
    whole=digest(json.dumps(rows,ensure_ascii=False).encode())
    actual=[{'case':r['case'],'events':len(r['events']),'sha256':digest(json.dumps(r,ensure_ascii=False).encode())} for r in rows]
    return {'matches_recovered_artifact':whole==reference['original_artifact_sha256'] and actual==reference['case_digests'],
            'sha256':whole,'cases':len(rows),'events':sum(len(r['events']) for r in rows),
            'first_difference':first_difference(reference['case_digests'],actual)}

def mutation_controls(candidate,fixture,fixture_sha):
    results=[]
    for mode in ('species','balance','order'):
        changed=copy.deepcopy(candidate)
        frame=next(f for c in changed['scenarios'] for f in c['timeline'] if len(f['events'])>=2)
        if mode=='species':frame['events'][0]['species_id']='synthetic_negative_species'
        elif mode=='balance':frame['state']['moedas_centavos']+=1
        else:frame['events'][0],frame['events'][1]=frame['events'][1],frame['events'][0]
        report=compare_runs(candidate,changed,fixture,fixture_sha)
        results.append({'mutation':mode,'expected_exit':1,'observed_exit':0 if report['equivalent'] else 1,
                        'first_difference':report['first_difference']})
    return results

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',default=BASE);ap.add_argument('--candidate')
    ap.add_argument('--git',default='git');ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--fixtures',type=Path,default=FIXTURES);ap.add_argument('--timeout',type=float,default=180)
    ap.add_argument('--compare-records',nargs=2,type=Path,metavar=('LEFT','RIGHT'))
    args=ap.parse_args(argv)
    created=False
    started=time.perf_counter()
    try:
        if args.timeout<=0:raise ValueError('Timeout must be positive')
        out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
        created=True
        fixture=read(args.fixtures);fixture_sha=digest(args.fixtures.read_bytes())
        if args.compare_records:
            left=read(args.compare_records[0]);right=read(args.compare_records[1])
            report=compare_runs(left,right,fixture,fixture_sha)
            report.update(base_sha=left['revision'],candidate_sha=right['revision'],fixture_sha256=fixture_sha,
                          versions={'left':left['versions'],'right':right['versions']})
            code=0 if report['equivalent'] else 1
        else:
            if args.base!=BASE or fixture['fixed_base']!=BASE:raise ValueError('This delivery requires the fixed documented base '+BASE)
            if not args.candidate:raise ValueError('--candidate FULL_SHA is required')
            if not re.fullmatch('[0-9a-f]{40}',args.candidate):raise ValueError('Use a full candidate SHA')
            work=out/'work';work.mkdir()
            left=execute_worker(args.git,args.base,'base',work,args.fixtures.resolve(),args.timeout)
            right=execute_worker(args.git,args.candidate,'candidate',work,args.fixtures.resolve(),args.timeout)
            repeated=execute_worker(args.git,args.candidate,'candidate_self',work,args.fixtures.resolve(),args.timeout)
            report=compare_runs(left,right,fixture,fixture_sha)
            self_report=compare_runs(right,repeated,fixture,fixture_sha)
            self_raw_diff=first_difference(right['scenarios'],repeated['scenarios'])
            controls=mutation_controls(right,fixture,fixture_sha)
            reference=read(REFERENCE)
            if digest((REFERENCE.parent/'comparador-original-20261018.py.txt').read_bytes())!=reference['original_script_sha256']:
                raise ValueError('Recovered original script hash mismatch')
            history={'base':historical_status(left,reference),'candidate':historical_status(right,reference)}
            report.update(base_sha=args.base,candidate_sha=args.candidate,fixture_sha256=fixture_sha,
                versions={'base':left['versions'],'candidate':right['versions'],'self':repeated['versions']},platform=platform.platform(),
                positive_control={'left_sha':args.candidate,'right_sha':args.candidate,
                    'equivalent':self_report['equivalent'] and self_raw_diff is None,'raw_first_difference':self_raw_diff},
                negative_controls=controls,historical_reproduction=history,
                pools_compared=len(right['catalogue']['pools']),
                source_assets_unchanged=True)
            report['schemas']={'base':left['schema'],'candidate':right['schema']}
            report['workers']=[read(work/(role+'-execution.json')) for role in ('base','candidate','candidate_self')]
            report['tool_hashes']={p.name:digest(p.read_bytes()) for p in (Path(__file__),ROOT/'tools/comparacao_worker.py')}
            if not report['positive_control']['equivalent'] or any(c['observed_exit']!=1 for c in controls):
                raise RuntimeError('Comparator controls failed')
            code=0 if report['equivalent'] and all(v['matches_recovered_artifact'] for v in history.values()) else 1
            if code and report['first_difference'] is None:
                side=next(k for k,v in history.items() if not v['matches_recovered_artifact'])
                report['first_difference']={'path':'$.historical_reference.'+side,
                    'reason':'recovered artifact mismatch','details':history[side]}
        report['executed_at_utc']=datetime.now(timezone.utc).isoformat()
        report['elapsed_seconds']=time.perf_counter()-started
        report['exit_code']=code;dump(out/'resultado.json',report)
        for row in report['scenarios']:
            print(row['id']+': '+('EQUIVALENTE' if row['equivalent'] else 'DIVERGENTE')+
                  f" events={row['base_events']}/{row['candidate_events']} rng_calls={row['rng_random_calls']} measured={row['candidate_additions']['measured_events']}")
        print(json.dumps({'exit_code':code,'first_difference':report['first_difference'],
                          'scenarios':len(report['scenarios']),'report':str(out/'resultado.json')},ensure_ascii=False))
        return code
    except Exception as exc:
        message={'exit_code':2,'error':type(exc).__name__,'message':str(exc)}
        if created:dump(out/'erro.json',message)
        print(json.dumps(message,ensure_ascii=False),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
