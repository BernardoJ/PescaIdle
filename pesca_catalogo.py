"""Immutable species and location occurrences loaded from one production source."""
import json
import math
from pathlib import Path
import sys
from pesca_tempo import LABELS

ASSETS = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets'
DATA = json.loads((ASSETS / 'catalogo_expansao.json').read_text(encoding='utf-8'))
VERSION = DATA['version']
ESPECIES = {s['id']: s for s in DATA['species']}
LOCAIS = {m['id']: m for m in DATA['maps']}
OCORRENCIAS = tuple(DATA['occurrences'])
LEGADO_49 = frozenset(DATA['legacy_collection'])
EXPANSAO_88 = frozenset(DATA['expansion_collection'])
ALIASES = {alias: s['id'] for s in ESPECIES.values() for alias in [s['nome'], *s['aliases']]}
INICIAL = 'enseada_do_poente'


def validate_catalogue():
    if len(ESPECIES) != len(DATA['species']) or len(LOCAIS) != len(DATA['maps']):
        raise ValueError('IDs repetidos no catálogo.')
    seen = set()
    for o in OCORRENCIAS:
        key = o['species_id'], o['map_id']
        if key in seen or o['species_id'] not in ESPECIES or o['map_id'] not in LOCAIS:
            raise ValueError(f'Ocorrência inválida: {key}')
        seen.add(key)
        if not o['periods'] or set(o['periods']) - set(LABELS):
            raise ValueError(f'Períodos inválidos: {key}')
        if not math.isfinite(o['weight']) or o['weight'] <= 0:
            raise ValueError(f'Peso inválido: {key}')
        if any(not math.isfinite(v) or v <= 0 for v in o['preferences'].values()):
            raise ValueError(f'Preferência inválida: {key}')
        if set(o['preferences'])-set(o['periods']):
            raise ValueError(f'Preferência fora da disponibilidade: {key}')
    for s in ESPECIES.values():
        if not math.isfinite(s['valor']) or s['valor'] < 0:
            raise ValueError('Valor inválido: '+s['id'])
    for m in LOCAIS:
        trash=LOCAIS[m]['trash_probability'];special=LOCAIS[m]['special_probability']
        if not all(math.isfinite(x) and 0<=x<1 for x in (trash,special)) or trash+special>=1:
            raise ValueError('Probabilidades de categoria inválidas: '+m)
        for p in LABELS:
            if len(eligible(m, p, 'peixe')) < 3:
                raise ValueError(f'Menos de três peixes: {m}/{p}')


def eligible(map_id, period_id, category=None):
    return tuple(o for o in OCORRENCIAS if o['map_id'] == map_id and period_id in o['periods']
                 and (category is None or ESPECIES[o['species_id']]['categoria'] == category))


def probabilities(map_id, period_id, rod_level=0):
    if map_id not in LOCAIS or period_id not in LABELS:
        raise ValueError('Contexto de pesca desconhecido.')
    fish = eligible(map_id, period_id, 'peixe')
    specials = eligible(map_id, period_id, 'especial')
    trash_chance = LOCAIS[map_id]['trash_probability']
    special_chance = LOCAIS[map_id]['special_probability'] if specials else 0
    result = {'bota_velha': trash_chance}
    for pool, share in ((fish, 1-trash_chance-special_chance), (specials, special_chance)):
        if not pool:
            continue
        weights = [o['weight'] * o['preferences'].get(period_id, 1.0)
                   * (1+.15*rod_level if ESPECIES[o['species_id']]['rod_bonus'] else 1) for o in pool]
        mass = sum(weights)
        if mass <= 0 or not math.isfinite(mass):
            raise ValueError('Pool sem massa finita.')
        result.update((o['species_id'], share*w/mass) for o, w in zip(pool, weights))
    return result


def desbloquear(state):
    unlocked = set(state.get('locais_desbloqueados', [])) & set(LOCAIS)
    unlocked.update(m['id'] for m in LOCAIS.values() if state['barco'] >= m['nivel_barco'])
    state['locais_desbloqueados'] = [id_ for id_ in LOCAIS if id_ in unlocked]
    if state.get('local_atual_id') not in unlocked:
        old = state.get('local_atual_id')
        if old:
            state.setdefault('diagnosticos_migracao', {})['local_anterior_invalido'] = old
        state['local_atual_id'] = INICIAL


def legacy_view(state):
    """Derived display projection, never a second persisted source of inventory."""
    return {**state.get('inventario_legado_desconhecido', {}),
            **{ESPECIES[id_]['nome']: count for id_, count in state['inventario_por_id'].items()
               if id_ in ESPECIES}}


validate_catalogue()
