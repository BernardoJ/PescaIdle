"""Reproduce the bounded base/ameno/weather study; real engines, synthetic data."""
import argparse,copy,json,math,os,statistics,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='c545ca652386d74372307bd6d52a91f84d1ed4a0'

def analyze(out):
    modes={mode:json.loads((out/(mode+'.json')).read_text(encoding='utf-8')) for mode in ['base','ameno','clima']}
    assert all(len(m['runs'])==70 and m['horizon_seconds']==86400 for m in modes.values())
    keys=['trial','seed','start_hour','cadence_seconds','events','total_gain_cents','upgrade_spent_cents','balance_cents',
          'known_species','encyclopedia10','regional_pairs','ledger_sha256','rng_sha256','inventory','milestones']
    for old,new in zip(modes['base']['runs'],modes['ameno']['runs']):
        for key in keys:
            if old[key]!=new[key]:raise AssertionError(f'Primeira diferença: perfil {old["trial"]}, intervalo {old["cadence_seconds"]}, campo {key}')
    by_mode={}
    for mode,m in modes.items():
        by_mode[mode]={}
        for cadence in [10800,1800]:
            rows=[r for r in m['runs'] if r['cadence_seconds']==cadence]
            by_mode[mode][str(cadence)]={}
            for key in ['total_gain_cents','balance_cents','known_species','encyclopedia10','regional_pairs','events']:
                values=[r[key] for r in rows]
                by_mode[mode][str(cadence)][key]=dict(mean=statistics.mean(values),median=statistics.median(values),min=min(values),max=max(values))
            for mark in ['rod10','boat10','funds_all_shop']:
                values=[r['milestones'][mark] for r in rows if r['milestones'][mark] is not None]
                by_mode[mode][str(cadence)][mark]=dict(reached=len(values),total=len(rows),median_seconds=statistics.median(values) if values else None)
    paired={}
    for cadence in [10800,1800]:
        base=[r for r in modes['base']['runs'] if r['cadence_seconds']==cadence]
        weather=[r for r in modes['clima']['runs'] if r['cadence_seconds']==cadence]
        paired[str(cadence)]={}
        for metric in ['total_gain_cents','known_species','encyclopedia10','regional_pairs']:
            diffs=[new[metric]-old[metric] for old,new in zip(base,weather)]
            ratios=[100*(new[metric]/old[metric]-1) for old,new in zip(base,weather) if old[metric]]
            mean=statistics.mean(diffs);se=statistics.stdev(diffs)/math.sqrt(len(diffs))
            paired[str(cadence)][metric]=dict(mean_difference=mean,mean_relative_percent=statistics.mean(ratios),median_difference=statistics.median(diffs),
                difference_ci95_normal_approx=[mean-1.96*se,mean+1.96*se])
    frequent_advantage={}
    for mode,m in modes.items():
        slow={r['trial']:r for r in m['runs'] if r['cadence_seconds']==10800}
        quick={r['trial']:r for r in m['runs'] if r['cadence_seconds']==1800}
        frequent_advantage[mode]={metric:dict(mean_difference=statistics.mean(quick[i][metric]-slow[i][metric] for i in slow),
            mean_relative_percent=statistics.mean(100*(quick[i][metric]/slow[i][metric]-1) for i in slow if slow[i][metric]))
            for metric in ['total_gain_cents','known_species','encyclopedia10','regional_pairs']}
    report=dict(base_sha=BASE,unique_initial_conditions=35,policies=2,runs_per_mode=70,modes=3,
        horizon_seconds=86400,total_actual_events=sum(r['events'] for m in modes.values() for r in m['runs']),
        base_ameno_exact=True,by_mode=by_mode,paired_weather_vs_base=paired,frequent_advantage=frequent_advantage,
        worker_seconds={k:m['seconds'] for k,m in modes.items()},
        interpretation='35 sementes/horários pareados por política. Revisão de destino por renda esperada a cada 3h ou 30min; não exige que o mapa mude em toda revisão. São heurísticas, sem prova de ótimo.',
        limits='Horizonte de 24h online; não mede conclusão integral, retenção, Android nem offline. Saldo suficiente para compras é um marco, não compra automática dos cosméticos. IC95 normal aproximado com 35 pares, condicionado ao modelo.')
    (out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['base_ameno_exact','total_actual_events','paired_weather_vs_base','frequent_advantage']},ensure_ascii=False))
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--analyze-existing',action='store_true');args=ap.parse_args();out=args.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out==ROOT/'qa':ap.error('Use pasta dentro de qa deste candidato.')
    if not args.analyze_existing:
        if args.base is None:ap.error('--base deve apontar para o checkout fixo c545ca6.')
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.base,text=True).strip()
        if head!=BASE:ap.error('Checkout-base não corresponde ao SHA fixo.')
        out.mkdir(parents=True,exist_ok=False)
        for mode in ['base','ameno','clima']:
            command=[sys.executable,'-X','utf8','-B',str(ROOT/'tools/climate_compare_worker.py'),'--source',str(args.base if mode=='base' else ROOT),'--out',str(out/(mode+'.json')),'--mode',mode]
            with (out/(mode+'.log')).open('w',encoding='utf-8') as log:
                subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
    analyze(out);return 0

if __name__=='__main__':raise SystemExit(main())
