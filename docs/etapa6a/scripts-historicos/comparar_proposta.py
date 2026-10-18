"""Design arithmetic only. Does not patch the engine or implement equipment."""
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'snapshot-verificado'
OUT = ROOT / 'analise'
OUT.mkdir(exist_ok=False)
sys.stdout.reconfigure(encoding='utf-8')
TEMP = tempfile.TemporaryDirectory(prefix='contas-proposta-', dir=ROOT / 'qa/temporarios')
os.environ.update(PESCA_IDLE_SAVE_PATH=str(Path(TEMP.name) / 'guard.json'),
                  APPDATA=str(Path(TEMP.name) / 'appdata'),
                  LOCALAPPDATA=str(Path(TEMP.name) / 'localappdata'))
sys.dont_write_bytecode = True
sys.path.insert(0, str(SOURCE))
from pesca_catalogo import ESPECIES, LOCAIS, OCORRENCIAS, probabilities
from pesca_moedas import reward
from pesca_tempo import PERIODOS

PILOT = 'enseada_do_poente'
FREQUENT = frozenset(('lambari', 'tilapia_do_nilo', 'carpa_comum', 'acara'))
TARGET = frozenset(('pacu', 'carpa_capim', 'traira', 'jundia'))
FACTORS = {'neutra': (1., 1.), 'fluxo': (1.25, .85), 'precisao': (.9, 1.5)}
pilot = [o for o in OCORRENCIAS if o['map_id'] == PILOT]
assert set(o['species_id'] for o in pilot) == FREQUENT | TARGET
assert all(o['weight'] >= 3 for o in pilot if o['species_id'] in FREQUENT)
assert all(o['weight'] < 3 for o in pilot if o['species_id'] in TARGET)
assert all(ESPECIES[id_]['raridade'] == 'Raro' for id_ in TARGET)


def proposed(base, map_id, choice):
    if map_id != PILOT or choice == 'neutra':
        return base.copy()
    result = base.copy()
    fish = {id_: p for id_, p in base.items()
            if id_ in ESPECIES and ESPECIES[id_]['categoria'] == 'peixe'}
    share = sum(fish.values())
    factors = FACTORS[choice]
    weights = {id_: p*factors[0 if id_ in FREQUENT else 1] for id_, p in fish.items()}
    mass = sum(weights.values())
    result.update({id_: share*w/mass for id_, w in weights.items()})
    return result


def distribution(values):
    values = sorted(values)
    pick = lambda q: values[round((len(values)-1)*q)]
    return dict(n=len(values), minimum=values[0], p10=pick(.1),
                median=statistics.median(values), p90=pick(.9), maximum=values[-1])


rows, samples = [], []
for map_id in LOCAIS:
    for period_id, _, _, _ in PERIODOS:
        for level in range(11):
            base = probabilities(map_id, period_id, level)
            for choice in FACTORS:
                probs = proposed(base, map_id, choice)
                assert set(probs) == set(base)
                assert all(math.isfinite(p) and p >= 0 for p in probs.values())
                assert math.isclose(sum(probs.values()), 1, rel_tol=0, abs_tol=1e-12)
                assert all(probs[id_] > 0 for id_ in base if base[id_] > 0)
                assert all(probs[id_] == p for id_, p in base.items()
                           if id_ not in ESPECIES or ESPECIES[id_]['categoria'] != 'peixe')
                if map_id != PILOT or choice == 'neutra':
                    assert probs == base
                if map_id != PILOT:
                    continue
                row = dict(map=map_id, period=period_id, rod=level, boat=level, choice=choice,
                           probabilities=probs,
                           target_share=sum(probs.get(id_, 0) for id_ in TARGET),
                           frequent_share=sum(probs.get(id_, 0) for id_ in FREQUENT),
                           expected_cents_per_event=sum(p*reward(ESPECIES[id_]['valor'], level)
                               for id_, p in probs.items() if id_ in ESPECIES),
                           expected_fish_species_in_100=sum(1-(1-p)**100 for id_, p in probs.items()
                               if id_ in ESPECIES and ESPECIES[id_]['categoria'] == 'peixe'))
                row['expected_coins_per_hour'] = row['expected_cents_per_event']/100*3600/(15/(1+.15*level)+1.5)
                rows.append(row)
                if level not in (0, 3, 10):
                    continue
                records = []
                for seed in range(30):
                    draws = random.Random(seed).choices(list(probs), weights=list(probs.values()), k=100)
                    records.append(dict(seed=seed,
                        gain_cents=sum(reward(ESPECIES[id_]['valor'], level) for id_ in draws if id_ in ESPECIES),
                        target_count=sum(id_ in TARGET for id_ in draws),
                        frequent_count=sum(id_ in FREQUENT for id_ in draws),
                        fish_count=sum(id_ in ESPECIES for id_ in draws),
                        fish_diversity=len(set(draws) & set(ESPECIES))))
                samples.append(dict(period=period_id, rod=level, boat=level, choice=choice,
                                    records=records,
                                    gain_cents=distribution([r['gain_cents'] for r in records]),
                                    target_count=distribution([r['target_count'] for r in records]),
                                    frequent_count=distribution([r['frequent_count'] for r in records]),
                                    fish_diversity=distribution([r['fish_diversity'] for r in records])))

# Explain time-of-day differences without changing the catalogue.
context = [row for row in rows if row['choice'] == 'neutra' and row['rod'] in (0, 3, 10)]
report = dict(source_commit='2a0353ff7c1cae2dca69d08c222b0660770d4385',
              catalogue_sha256=hashlib.sha256((SOURCE / 'assets/catalogo_expansao.json').read_bytes()).hexdigest(),
              pilot=PILOT, frequent_ids=sorted(FREQUENT), target_ids=sorted(TARGET), factors=FACTORS,
              exact_pool_scenarios=8*7*11*3, exact_pilot_rows=rows,
              seeded_fixed_pool_scenarios=len(samples)*30, draws_per_seed=100, seeds=list(range(30)),
              seeded_fixed_pool=samples, neutral_period_context=context,
              limits=['Design calculations, not implemented equipment or a post-implementation test.',
                      '100 independent results in a frozen period, not 100 timed fishing events or four real hours.',
                      'Hourly expectations hold a period and equipment fixed; not calendar forecasts.',
                      'Same timing and category shares; only conditional fish weights change in the proposed pilot.',
                      'No game RNG, personal profile, SaveStore, production mutation or pending event edited.'])
(OUT / 'proposta-pesos.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
short = [dict(period=r['period'], level=r['rod'], choice=r['choice'],
              rare_percent=round(r['target_share']*100, 4),
              income_hour=round(r['expected_coins_per_hour'], 4),
              diversity_100=round(r['expected_fish_species_in_100'], 4))
         for r in rows if r['rod'] == 0]
print(json.dumps(dict(exact_pool_scenarios=report['exact_pool_scenarios'],
                     seeded_scenarios=report['seeded_fixed_pool_scenarios'], level0=short), ensure_ascii=False))
TEMP.cleanup()
