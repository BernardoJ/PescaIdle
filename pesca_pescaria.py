"""Deterministic event core shared by active time and historical offline replay."""
import copy
from decimal import Decimal
import math
import random
from pesca_catalogo import ESPECIES, LOCAIS, VERSION, probabilities, legacy_view, desbloquear
from pesca_tempo import snapshot


def as_tuple(value):
    return tuple(as_tuple(x) for x in value) if isinstance(value, (list, tuple)) else value


class FishingEngine:
    def __init__(self, state, rng=None):
        self.state = copy.deepcopy(state)
        self.rng = rng or random.Random()
        if rng is None and state.get('rng_state') is not None:
            self.rng.setstate(as_tuple(state['rng_state']))
        self.events = []
        if self.state['pesca']['restante'] is None:
            self.wait()

    def wait(self):
        self.state['pesca'] = {'etapa': 'aguardando',
            'restante': self.rng.uniform(10, 20)/(1+.15*self.state['vara'])}

    def begin_strike(self, utc, offset, map_id=None, equipment=None):
        if self.state['pesca_pendente'] is not None:
            raise ValueError('Já existe uma fisgada pendente.')
        context = snapshot(utc, offset)
        context.update(map_id=map_id or self.state['local_atual_id'],
                       vara=self.state['vara'], barco=self.state['barco'], catalog_version=VERSION)
        if equipment:
            context.update(equipment)
        probs = probabilities(context['map_id'], context['periodo_id'], context['vara'])
        species_id = self.rng.choices(list(probs), weights=list(probs.values()))[0]
        self.state['contador_eventos'] += 1
        event = {'id': f"{self.state['perfil_id']}:{self.state['contador_eventos']}",
                 'species_id': species_id, 'context': context, 'gain': 0,
                 'categoria': 'lixo' if species_id == 'bota_velha' else ESPECIES[species_id]['categoria']}
        if species_id in ESPECIES:
            event['gain'] = round(ESPECIES[species_id]['valor']*(1+.2*context['barco']), 2)
        self.state['pesca_pendente'] = event
        self.state['pesca'] = {'etapa': 'fisgando', 'restante': 1.5}
        return event

    def finish_strike(self):
        event = self.state['pesca_pendente']
        if event is None:
            raise ValueError('Fisgada sem resultado persistido.')
        if event['id'] != self.state['ultimo_evento_aplicado']:
            if event['species_id'] in ESPECIES:
                self.state['moedas'] = float(Decimal(str(self.state['moedas'])) + Decimal(str(event['gain'])))
                self.state['total_pescados'] += 1
                inv = self.state['inventario_por_id']; id_ = event['species_id']
                inv[id_] = inv.get(id_, 0)+1
                ctx = event['context']
                regional = self.state['registros_regionais'].setdefault(ctx['map_id'], {})
                regional[id_] = regional.get(id_, 0)+1
                temporal = self.state['registros_por_periodo'].setdefault(ctx['map_id'], {}).setdefault(ctx['periodo_id'], {})
                temporal[id_] = temporal.get(id_, 0)+1
            self.state['ultimo_evento_aplicado'] = event['id']
            self.events.append(copy.deepcopy(event))
        self.state['pesca_pendente'] = None
        if self.state['viagem_pendente']:
            self.state['local_atual_id'] = self.state['viagem_pendente']
            self.state['viagem_pendente'] = None
        self.wait()

    def advance(self, seconds, start_utc, offset, map_id=None, equipment=None):
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError('Intervalo de simulação inválido.')
        remaining = seconds; cursor = start_utc
        while remaining > 1e-9:
            phase = self.state['pesca']
            amount = min(remaining, max(0, phase['restante']))
            phase['restante'] -= amount; cursor += amount; remaining -= amount
            if phase['restante'] <= 1e-9:
                if phase['etapa'] == 'aguardando':
                    self.begin_strike(cursor, offset, map_id, equipment)
                else:
                    self.finish_strike()
        self.state['rng_state'] = self.rng.getstate()
        self.state['inventario'] = legacy_view(self.state)
        return self.state


def travel(state, map_id):
    if map_id not in LOCAIS or map_id not in state['locais_desbloqueados']:
        return False
    if state['pesca_pendente']:
        state['viagem_pendente'] = map_id
    else:
        state['local_atual_id'] = map_id
    return True
