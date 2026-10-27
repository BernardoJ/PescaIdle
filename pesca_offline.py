"""Single absence budget: normal replay OR an optional one-shot expedition."""
import copy
import math
import uuid
from pesca_catalogo import LOCAIS
from pesca_pescaria import FishingEngine
from pesca_moedas import balance

LIMIT = 14400


def schedule(state, map_id, start, duration, now):
    if map_id not in state['locais_desbloqueados'] or map_id not in LOCAIS:
        raise ValueError('Expedição requer um mapa desbloqueado.')
    if not all(math.isfinite(x) for x in (start, duration, now)) or not 0 < start-now <= 86400 or not 0 < duration <= LIMIT:
        raise ValueError('Escolha início nas próximas 24h e duração de até 4h.')
    state['expedicao'] = {'id': uuid.uuid4().hex, 'status': 'agendada', 'map_id': map_id,
                         'inicio_utc': start, 'duracao': duration, 'processado_ate': None}


def cancel(state):
    if state.get('expedicao') and state['expedicao']['status'] == 'agendada':
        state['expedicao']['status'] = 'cancelada'


def expire_active(state, now):
    plan = state.get('expedicao')
    if plan and plan['status'] == 'agendada' and now >= plan['inicio_utc']:
        plan['status'] = 'expirada'


def replay(state, now):
    candidate = copy.deepcopy(state)
    start = candidate['ultimo_processado_utc']
    elapsed = max(0, now-start)
    candidate['ultimo_processado_utc'] = max(start, now)
    report = {'mode': 'normal', 'elapsed': elapsed, 'paid_seconds': 0,
              'discarded': 0, 'count': 0, 'gain': 0, 'events': []}
    if elapsed == 0 or candidate['pausado']:
        report['mode'] = 'pausado' if candidate['pausado'] else 'normal'
        return candidate, report
    offset = candidate['contexto_fuso']
    plan = candidate.get('expedicao')
    lo, hi = start, min(now, start+LIMIT)
    override = None
    if plan and plan['status'] == 'agendada':
        report['mode'] = 'expedicao'
        if plan['inicio_utc'] < start:
            plan['status'] = 'expirada'; lo = hi = start
        elif now < plan['inicio_utc']:
            lo = hi = start  # Future schedule survives an early return.
        else:
            lo, hi = max(start, plan['inicio_utc']), min(now, plan['inicio_utc']+plan['duracao'])
            override = plan['map_id']
            plan['status'] = 'consumida'
            plan['processado_ate'] = hi
    budget = max(0, hi-lo)
    report['paid_seconds'] = budget
    report['discarded'] = elapsed-budget
    before = balance(candidate)
    engine = FishingEngine(candidate)
    candidate = engine.advance(budget, lo, offset, override,
                               {'vara': candidate['vara'], 'barco': candidate['barco']})
    report.update(count=sum(e['categoria']!='lixo' for e in engine.events),cycles=len(engine.events),
                  gain=(balance(candidate)-before)/100,events=engine.events)
    return candidate, report
