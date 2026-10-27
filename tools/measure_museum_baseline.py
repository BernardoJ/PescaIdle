"""Small seeded measurement of the current rules, never a balancing patch."""
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(os.environ.get('PESCA_IDLE_MEASURE_SOURCE', Path(__file__).resolve().parents[1])).resolve()
sys.path.insert(0, str(ROOT))


def distribution(values):
    ordered = sorted(values)
    if not ordered:
        return None
    def quantile(q):
        return ordered[min(len(ordered)-1, int((len(ordered)-1)*q+.5))]
    return dict(n=len(values), minimum=ordered[0], p10=quantile(.1),
                median=statistics.median(values), p90=quantile(.9),
                p95=quantile(.95), maximum=ordered[-1])


def measure(out):
    # No GUI import and no SaveStore. Use the actual literal game defaults.
    from pesca_save import migrate
    from pesca_catalogo import ESPECIES, LOCAIS, OCORRENCIAS, desbloquear
    from pesca_pescaria import FishingEngine
    from pesca_offline import replay
    from pesca_moedas import debit, can_buy, balance
    from pesca_tempo import PERIODOS
    tree = ast.parse((ROOT/'pesca_idle.py').read_text(encoding='utf-8-sig'))
    defaults = next(ast.literal_eval(n.value) for n in tree.body
                    if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict)
                    and any(isinstance(t, ast.Name) and t.id == 'ESTADO_PADRAO' for t in n.targets))
    source_files = ('pesca_idle.py', 'pesca_pescaria.py', 'pesca_offline.py',
                    'pesca_moedas.py', 'pesca_save.py', 'assets/catalogo_expansao.json')
    hashes = {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in source_files}
    seeds = list(range(30))
    def fresh(seed, start, level=0, location='enseada_do_poente'):
        s = migrate({}, defaults, start)
        s.update(perfil_id='synthetic-measure-'+str(seed), contexto_fuso=0,
                 vara=level, barco=level, local_atual_id=location,
                 rng_state=random.Random(seed).getstate())
        desbloquear(s)
        return s

    def run(seed, start, level, location, buying=False, duration=14400):
        e = FishingEngine(fresh(seed, start, level, location))
        regional = {o['species_id'] for o in OCORRENCIAS if o['map_id'] == location}
        elapsed = 0
        attempts = 0
        milestones = {}
        cumulative = 0
        trajectory = []
        def reached(name):
            milestones.setdefault(name, {'seconds': elapsed, 'attempts': attempts})
        for checkpoint in (600, 1800, 3600, duration):
            while elapsed < checkpoint-1e-8:
                step = min(e.state['pesca']['restante'], checkpoint-elapsed)
                e.advance(step, start+elapsed, 0)
                elapsed += step
                attempts += len(e.events)
                cumulative += sum(x['gain_cents'] for x in e.events)
                e.events.clear()
                inv = e.state['inventario_por_id']
                if sum(ESPECIES[id_]['categoria']=='peixe' for id_ in inv) >= 3:
                    reached('aquario_3_especies')
                if sum(ESPECIES[id_]['categoria']=='peixe' for id_ in inv) >= 5:
                    reached('cinco_peixes_distintos')
                if regional <= set(inv):
                    reached('colecao_regional_completa')
                if buying:
                    # Alternate complete rod/boat levels. Prices and thresholds
                    # match comprar_peca; pending strikes keep their frozen gear.
                    while True:
                        kind = 'vara' if e.state['vara'] <= e.state['barco'] else 'barco'
                        if e.state[kind] >= 10:
                            break
                        price = 30+20*e.state[kind]
                        if not can_buy(e.state, price):
                            break
                        reached('primeira_peca')
                        debit(e.state, price)
                        e.state['pecas_'+kind] += 1
                        needed = 2+e.state[kind]
                        if e.state['pecas_'+kind] >= needed:
                            e.state['pecas_'+kind] -= needed
                            e.state[kind] += 1
                            reached(kind+'_'+str(e.state[kind]))
                            previous = set(e.state['locais_desbloqueados'])
                            desbloquear(e.state)
                            for map_id in set(e.state['locais_desbloqueados'])-previous:
                                reached('local_'+map_id)
                e.state['ultimo_processado_utc'] = start+elapsed
            trajectory.append(dict(seconds=checkpoint, gain_cents=cumulative,
                                   balance_cents=balance(e.state), attempts=attempts,
                                   catches=e.state['total_pescados'],
                                   diversity=len(e.state['inventario_por_id']),
                                   rod=e.state['vara'], boat=e.state['barco']))
        return dict(seed=seed, milestones=milestones, checkpoints=trajectory,
                    missing_regional=sorted(regional-set(e.state['inventario_por_id'])))

    profiles = []
    for period_id, _, hour, _ in PERIODOS:
        start = datetime(2026, 10, 15, hour, tzinfo=timezone.utc).timestamp()
        records = [run(seed, start, 0, 'enseada_do_poente', True) for seed in seeds]
        names = sorted(set().union(*(r['milestones'] for r in records),
            {'primeira_peca','aquario_3_especies','cinco_peixes_distintos','colecao_regional_completa'},
            {kind+'_'+str(level) for kind in ('vara','barco') for level in range(1,11)},
            {'local_'+id_ for id_ in LOCAIS if id_!='enseada_do_poente'}))
        summary = {}
        for name in names:
            completed = [r['milestones'][name] for r in records if name in r['milestones']]
            summary[name] = dict(reached=len(completed), censored=30-len(completed),
                                 seconds_completed_only=distribution([r['seconds'] for r in completed]),
                                 attempts_completed_only=distribution([r['attempts'] for r in completed]))
        profiles.append(dict(start_period=period_id, policy='alternate complete rod/boat levels, no travel or cosmetics',
                             horizon_seconds=14400, summaries=summary, records=records))
        print('Progression:', period_id, flush=True)

    tiers = []
    start = datetime(2026, 10, 15, 9, tzinfo=timezone.utc).timestamp()
    for level, location in ((0,'enseada_do_poente'), (3,'pier_da_brisa'), (10,'fossa_das_lanternas')):
        records = [run(seed, start, level, location) for seed in seeds]
        tiers.append(dict(level=level, map=location, policy='fixed equipment, no purchases or travel', records=records,
                          gain_cents=distribution([r['checkpoints'][-1]['gain_cents'] for r in records]),
                          catches=distribution([r['checkpoints'][-1]['catches'] for r in records]),
                          diversity=distribution([r['checkpoints'][-1]['diversity'] for r in records])))
    returns = []
    def equivalent(a, b):
        if any(a[k] != b[k] for k in ('moedas_centavos','inventario_por_id','rng_state')):
            return False
        if a['pesca']['etapa'] != b['pesca']['etapa'] or not math.isclose(
                a['pesca']['restante'], b['pesca']['restante'], rel_tol=0, abs_tol=1e-6):
            return False
        left, right = copy.deepcopy(a['pesca_pendente']), copy.deepcopy(b['pesca_pendente'])
        if left is None or right is None:
            return left == right
        for key in ('utc','local_iso'):
            x, y = left['context'].pop(key), right['context'].pop(key)
            if key == 'local_iso':
                x, y = datetime.fromisoformat(x).timestamp(), datetime.fromisoformat(y).timestamp()
            if not math.isclose(x, y, rel_tol=0, abs_tol=.0001):
                return False
        return left == right
    for seed in seeds:
        initial = fresh(seed, start, 3, 'pier_da_brisa')
        for duration in (3600, 14400, 28800):
            online = FishingEngine(initial)
            continuous = online.advance(duration, start, 0)
            offline, report = replay(initial, start+duration)
            hourly = copy.deepcopy(initial)
            for t in range(3600, duration+1, 3600):
                hourly, _ = replay(hourly, start+t)
            one_equal = equivalent(continuous, offline)
            hourly_equivalent = equivalent(continuous, hourly)
            if duration <= 14400 and not one_equal or not hourly_equivalent:
                raise RuntimeError('Active/offline equivalence failed')
            returns.append(dict(seed=seed, absent_seconds=duration, paid_seconds=report['paid_seconds'],
                                continuous_cents=balance(continuous), one_return_cents=balance(offline),
                                hourly_returns_cents=balance(hourly), equal_to_continuous=one_equal,
                                hourly_equal_to_continuous=hourly_equivalent))
    report = dict(source_runtime_sha256=hashes, seeds=seeds, python=sys.version,
                  simulated_date='2026-10-15', offset_seconds=0, progression=profiles,
                  return_comparison_tolerance={'remaining_seconds':1e-6,'pending_utc_seconds':.0001,
                    'exact':['money','inventory','RNG','pending result and period/equipment']},
                  fixed_profiles=tiers, return_comparison=returns,
                  limitations=['No economy changes. Synthetic profiles; no save read/write.',
                    'Four-hour horizon; incomplete goals are censored, never counted as completed.',
                    'Fixed offsets and scripted immediate purchases; not human behavior.',
                    'Regional completion includes specials; aquarium eligibility uses only category peixe.',
                    'No extrapolation to global collection, DST or physical battery/performance.'])
    out.mkdir(parents=True, exist_ok=True)
    (out/'ritmo.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Measured:', len(profiles)*30, 'progression runs,',len(tiers)*30,'fixed profiles,',len(returns),'return pairs.')


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='pesca-museum-measure-') as tmp:
        os.environ.update(PESCA_IDLE_SAVE_PATH=str(Path(tmp)/'guard.json'),
                          APPDATA=str(Path(tmp)/'appdata'), LOCALAPPDATA=str(Path(tmp)/'localappdata'))
        measure(Path(os.environ.get('PESCA_IDLE_QA_DIR', tmp)))
