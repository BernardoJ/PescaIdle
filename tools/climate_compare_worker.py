"""Bounded paired progressions using the real engine of one specified revision."""
import argparse,ast,copy,hashlib,inspect,json,os,random,sys,time
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import patch

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--mode',choices=['base','ameno','clima'],required=True)
    args=ap.parse_args();out=args.out.resolve();source=args.source.resolve(strict=True)
    if out.exists():raise RuntimeError('Saída existente; use arquivo novo.')
    guard=out.parent/('guard-'+args.mode);guard.mkdir(parents=True,exist_ok=False)
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(guard/'save.json'),APPDATA=str(guard/'appdata'),
        LOCALAPPDATA=str(guard/'localappdata'),TEMP=str(guard),TMP=str(guard),PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0,str(source))
    from pesca_catalogo import LOCAIS,ESPECIES,probabilities,desbloquear
    from pesca_save import migrate
    from pesca_tamanhos import empty_sizes
    from pesca_pescaria import FishingEngine,travel
    from pesca_moedas import reward,debit
    from pesca_tempo import snapshot
    has_weather='weather' in inspect.signature(probabilities).parameters
    if has_weather:
        from pesca_clima import context,new_climate
    assert has_weather==(args.mode!='base')
    if args.mode=='ameno':patcher=patch('pesca_clima.daily_id',return_value='ameno');patcher.start()
    tree=ast.parse((source/'pesca_idle.py').read_text(encoding='utf-8'))
    defaults=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ESTADO_PADRAO' for t in n.targets))
    rows=[];started=time.perf_counter();hours=[6,8,10,12,15,18,23]
    for cadence in [10800,1800]:
        for hi,hour in enumerate(hours):
            for si in range(5):
                trial=hi*5+si;seed=2026102300+trial
                start=datetime(2026,10,23,hour,tzinfo=timezone(timedelta(hours=-3))).timestamp()
                state=migrate({},defaults,start);state['perfil_id']='climate-balance-'+str(trial)
                state['medidas_peixes']=empty_sizes(state['perfil_id']);state['contexto_fuso']=-10800
                state['rng_state']=random.Random(seed).getstate()
                if has_weather:state['clima']=new_climate(state['perfil_id'],start)
                engine=FishingEngine(state);elapsed=0.;next_decision=0.;total_gain=0;events=0;spent=0
                ledger=hashlib.sha256();weather_counts={};milestones={k:None for k in ['rod10','boat10','funds_all_shop']}
                def choose():
                    s=engine.state;p=snapshot(start+elapsed,-10800)['periodo_id'];weather=context(s,start+elapsed,-10800)['id'] if has_weather else None
                    best=-1;chosen=s['local_atual_id']
                    for mid in s['locais_desbloqueados']:
                        probs=probabilities(mid,p,s['vara'],weather) if has_weather else probabilities(mid,p,s['vara'])
                        rate=sum(prob*reward(ESPECIES[id_]['valor'],s['barco']) for id_,prob in probs.items() if id_ in ESPECIES)
                        if rate>best:best=rate;chosen=mid
                    travel(s,chosen)
                choose();next_decision=cadence
                while elapsed<86400-1e-8:
                    remain=engine.state['pesca']['restante'];amount=min(remain,next_decision-elapsed,86400-elapsed)
                    engine.advance(amount,start+elapsed,-10800);elapsed+=amount
                    if engine.events:
                        event=engine.events.pop();assert not engine.events
                        events+=1;total_gain+=event['gain_cents'];ctx=event['context']
                        weather=ctx.get('clima',{}).get('id','base');weather_counts[weather]=weather_counts.get(weather,0)+1
                        ledger.update(json.dumps([event['species_id'],event['gain_cents'],round(ctx['utc'],6),ctx['vara'],ctx['barco'],event.get('measurement',{}).get('mm')],separators=(',',':')).encode())
                        s=engine.state;old_boat=s['barco']
                        while s['vara']<10 or s['barco']<10:
                            kind='vara' if s['vara']<=s['barco'] and s['vara']<10 else 'barco'
                            cost=30+20*s[kind]
                            if not debit(s,cost):break
                            spent+=cost*100;s['pecas_'+kind]+=1
                            if s['pecas_'+kind]>=2+s[kind]:s['pecas_'+kind]-=2+s[kind];s[kind]+=1;desbloquear(s)
                        for kind in ['vara','barco']:
                            key='rod10' if kind=='vara' else 'boat10'
                            if s[kind]==10 and milestones[key] is None:milestones[key]=elapsed
                        if s['vara']==s['barco']==10 and s['moedas_centavos']>=41989800 and milestones['funds_all_shop'] is None:milestones['funds_all_shop']=elapsed
                        if s['barco']!=old_boat:choose()
                    if abs(elapsed-next_decision)<1e-7:choose();next_decision+=cadence
                inv=engine.state['inventario_por_id']
                rows.append(dict(trial=trial,seed=seed,start_hour=hour,cadence_seconds=cadence,
                    events=events,total_gain_cents=total_gain,upgrade_spent_cents=spent,balance_cents=engine.state['moedas_centavos'],
                    known_species=sum(n>0 for n in inv.values()),encyclopedia10=sum(n>=10 for n in inv.values()),
                    regional_pairs=sum(n>0 for m in engine.state['registros_regionais'].values() for n in m.values()),
                    ledger_sha256=ledger.hexdigest(),rng_sha256=hashlib.sha256(repr(engine.rng.getstate()).encode()).hexdigest(),
                    inventory=inv,milestones=milestones,weather_event_counts=weather_counts))
        print(args.mode+': '+str(len(rows))+'/70',flush=True)
    out.write_text(json.dumps(dict(mode=args.mode,runs=rows,seconds=time.perf_counter()-started,horizon_seconds=86400,
        policy='Renda esperada, revisada a cada 3h ou 30min; upgrades imediatos; demais compras representadas por saldo suficiente, sem gastos cosméticos.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
