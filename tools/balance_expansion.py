"""Reproducible exact pools and seeded economy comparison; no personal profile."""
import ast
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import tempfile
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))


def percentile(values,q):
    values=sorted(values);return values[min(len(values)-1,math.ceil(q*len(values))-1)]


def run(out):
    from pesca_catalogo import DATA,ESPECIES,LOCAIS,probabilities
    from pesca_tempo import PERIODOS
    from pesca_save import migrate
    from pesca_moedas import can_buy,debit,reward
    from pesca_pescaria import FishingEngine
    tree=ast.parse((ROOT/'docs/design/pesca_idle_base_6b29b4a.py.txt').read_text(encoding='utf-8-sig'))
    literals={node.targets[0].id:ast.literal_eval(node.value) for node in tree.body
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('LOOT','ESTADO_PADRAO')}
    old=literals['LOOT'];defaults=literals['ESTADO_PADRAO'];seeds=list(range(30));rows=[]
    def earnings(id_,boat):return reward(ESPECIES[id_]['valor'],boat)/100 if id_ in ESPECIES else 0
    lengths=[2,2,2,3,3,3,9];daily={}
    for map_id in LOCAIS:
        for level in (0,3,10):
            weighted=0
            for (period_id,_,hour,_),hours in zip(PERIODOS,lengths):
                probs=probabilities(map_id,period_id,level);mean=sum(p*earnings(id_,level) for id_,p in probs.items())
                cycle=15/(1+.15*level)+1.5;hourly=mean*3600/cycle;weighted+=hourly*hours/24
                rng=random.Random(870+len(rows));n=int(3600/cycle)
                gains=[sum(earnings(id_,level) for id_ in rng.choices(list(probs),weights=list(probs.values()),k=n)) for _ in seeds]
                row={'map':map_id,'period':period_id,'rod':level,'boat':level,'exact_mean_event':mean,
                     'exact_variance_event':sum(p*(earnings(id_,level)-mean)**2 for id_,p in probs.items()),
                     'exact_mean_hour':hourly,'sample_hour_p10':percentile(gains,.1),
                     'sample_hour_median':statistics.median(gains),'sample_hour_p95':percentile(gains,.95),
                     'sample_seed':870+len(rows),'probabilities':{id_:probs.get(id_,0) for id_ in ['bota_velha',*ESPECIES]},
                     'category_probability':{cat:sum(p for id_,p in probs.items() if ('lixo' if id_=='bota_velha' else ESPECIES[id_]['categoria'])==cat) for cat in ('peixe','especial','lixo')},
                     'first_discovery_eligible_hours':{id_:{'mean':cycle/p/3600,'median':(1 if p==1 else math.ceil(math.log(.5)/math.log1p(-p)))*cycle/3600} for id_,p in probs.items() if p>0 and id_!='bota_velha'}}
                rows.append(row)
            daily[map_id+':'+str(level)]=weighted
    baseline_mean=sum(x['peso']*x.get('valor',0) for x in old)/sum(x['peso'] for x in old)
    progression=[]
    for period_id,_,hour,_ in PERIODOS:
        start=datetime(2026,10,6,hour,tzinfo=timezone.utc).timestamp();a=[];b=[]
        for seed in seeds:
            rng=random.Random(seed);balance=0;pieces=0;duration=0;cycles=0
            while pieces<2 and duration<259200:
                duration+=rng.uniform(10,20)+1.5
                item=rng.choices(old,weights=[x['peso'] for x in old])[0]
                balance+=item.get('valor',0);cycles+=1
                while balance>=30 and pieces<2:balance-=30;pieces+=1
            a.append(duration)
            state=migrate({},defaults,start);state['perfil_id']='balance-'+str(seed)
            engine=FishingEngine(state,random.Random(seed));duration=0;pieces=0
            while pieces<2 and duration<259200:
                step=engine.state['pesca']['restante'];engine.advance(step,start+duration,0);duration+=step
                while can_buy(engine.state,30) and pieces<2:debit(engine.state,30);pieces+=1
            b.append(duration)
        ratio=statistics.median(b)/statistics.median(a)
        progression.append({'start_period':period_id,'seeds':seeds,'baseline_seconds':a,'expansion_seconds':b,
                            'baseline_median':statistics.median(a),'expansion_median':statistics.median(b),
                            'ratio':ratio,'target_max_ratio':1.5,'passed':ratio<=1.5})
    report={'python':sys.version,'platform':platform.platform(),'catalogue_version':DATA['version'],
        'seeds':seeds,'policy':'Compra automática de duas peças de barco por 30 moedas cada; vara/barco 0; sem cosméticos.',
        'baseline_mean_event':baseline_mean,'baseline_mean_hour':baseline_mean*3600/16.5,
        'formulas':{'wait':'Uniforme(10,20)/(1+0.15*vara)','strike':1.5,'reward':'round(valor*(1+0.2*barco),2)'},
        'calendar_weights_hours':lengths,'weighted_24h_mean':daily,'pools':rows,'boat_1':progression,
        'limits':'Descobertas calculadas em tempo ativo elegível de um pool fixo. Tempo de calendário depende das janelas e viagens; não é equivalente. Níveis 3/10 em todos os mapas são cenários matemáticos, inclusive mapas bloqueados.'}
    out.mkdir(parents=True,exist_ok=True);(out/'balanceamento.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in progression:print(row['start_period'],round(row['baseline_median'],1),round(row['expansion_median'],1),round(row['ratio'],3),row['passed'])
    assert all(x['passed'] for x in progression),'BAL-02: first boat target failed'
    print('BAL-01/02: 168 exact pools + 7 progression starts × 30 seeds passed.')


if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='pesca-balance-') as tmp:
        os.environ['PESCA_IDLE_SAVE_PATH']=str(Path(tmp)/'save.json');os.environ['APPDATA']=str(Path(tmp)/'appdata')
        os.environ['LOCALAPPDATA']=str(Path(tmp)/'localappdata')
        run(Path(os.environ.get('PESCA_IDLE_QA_DIR',tmp)))
