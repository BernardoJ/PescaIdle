"""Versioned migration, exclusive profile writer and atomic durable snapshots."""
import copy
import json
import os
from pathlib import Path
import tempfile
import time
import uuid
import math
import random
from pesca_catalogo import ALIASES, ESPECIES, desbloquear, legacy_view
from pesca_tempo import snapshot

SCHEMA = 2


class SaveError(RuntimeError):
    pass


def migrate(raw, defaults, now):
    if not isinstance(raw, dict):
        raise SaveError('Save inválido: era esperado um objeto JSON.')
    version = raw.get('schema_version', 1)
    if type(version) is not int or version > SCHEMA or version < 1:
        raise SaveError('Versão do save não suportada; o arquivo foi preservado.')
    state = copy.deepcopy(defaults)
    state.update(copy.deepcopy(raw))
    # Session/profile fields must never inherit the module's import timestamp
    # or another profile's identity from an expanded defaults dictionary.
    dynamic = ('perfil_id', 'ultimo_processado_utc', 'contexto_fuso', 'pesca',
               'pesca_pendente', 'rng_state', 'expedicao', 'viagem_pendente',
               'registros_regionais', 'registros_por_periodo', 'legado_sem_contexto',
               'local_atual_id', 'locais_desbloqueados', 'contador_eventos',
               'ultimo_evento_aplicado', 'pausado')
    for key in dynamic:
        if key not in raw:
            state.pop(key, None)
    state['equipados'] = {**defaults['equipados'], **raw.get('equipados', {})}
    state['cosmeticos'] = list(dict.fromkeys([*raw.get('cosmeticos', []), *defaults['cosmeticos']]))
    state.setdefault('conquistas', [])
    if version == 1:
        inv = {}; unknown = {}
        for name, count in raw.get('inventario', {}).items():
            if name in ALIASES:
                id_ = ALIASES[name]; inv[id_] = inv.get(id_, 0)+count
            else:
                unknown[name] = count
        state['inventario_por_id'] = inv
        state['inventario_legado_desconhecido'] = unknown
        state['legado_sem_contexto'] = copy.deepcopy(inv)
    state.setdefault('inventario_por_id', {})
    state.setdefault('inventario_legado_desconhecido', {})
    state.setdefault('legado_sem_contexto', {})
    # Unknown future species IDs remain recoverable, without invented occurrences.
    state.setdefault('registros_regionais', {})
    state.setdefault('registros_por_periodo', {})
    state.setdefault('local_atual_id', 'enseada_do_poente')
    state.setdefault('locais_desbloqueados', [])
    state.setdefault('pausado', False)
    state.setdefault('perfil_id', uuid.uuid4().hex)
    state.setdefault('contador_eventos', 0)
    state.setdefault('ultimo_evento_aplicado', None)
    state.setdefault('ultimo_processado_utc', raw.get('ultimo_salvo') or now)
    state.setdefault('contexto_fuso', snapshot(now)['offset_seconds'])
    state.setdefault('pesca', {'etapa': 'aguardando', 'restante': None})
    state.setdefault('pesca_pendente', None)
    state.setdefault('viagem_pendente', None)
    state.setdefault('expedicao', None)
    state.setdefault('rng_state', None)
    state['schema_version'] = SCHEMA
    if not isinstance(state['inventario_por_id'], dict) or any(
            type(n) is not int or n < 0 for n in state['inventario_por_id'].values()):
        raise SaveError('Contagens inválidas; o save foi preservado.')
    validate_state(state)
    desbloquear(state)
    state['inventario'] = legacy_view(state)
    return state


def validate_state(state):
    for key in ('moedas','ultimo_processado_utc','contexto_fuso'):
        if type(state[key]) not in (int,float) or not math.isfinite(state[key]):
            raise SaveError('Campo numérico inválido: '+key)
    if state['moedas']<0:raise SaveError('Saldo inválido; save preservado.')
    for key in ('vara','barco','pecas_vara','pecas_barco','total_pescados','contador_eventos'):
        if type(state[key]) is not int or state[key]<0:raise SaveError('Contador inválido: '+key)
    if state['vara']>10 or state['barco']>10:raise SaveError('Nível de equipamento não suportado.')
    phase=state['pesca'];pending=state['pesca_pendente']
    if not isinstance(phase,dict) or phase.get('etapa') not in ('aguardando','fisgando'):
        raise SaveError('Etapa de pesca inválida.')
    remaining=phase.get('restante')
    if remaining is not None and (type(remaining) not in (int,float) or not math.isfinite(remaining) or remaining<0):
        raise SaveError('Tempo restante inválido.')
    if bool(pending)!=(phase['etapa']=='fisgando') or (pending and remaining is None):
        raise SaveError('Resultado pendente inconsistente; save preservado.')
    if pending:
        from pesca_catalogo import LOCAIS
        from pesca_tempo import LABELS
        try:
            context=pending['context']
            if not (pending['species_id'] in ESPECIES or pending['species_id']=='bota_velha'):
                raise ValueError('espécie inválida')
            if context['map_id'] not in LOCAIS or context['periodo_id'] not in LABELS:
                raise ValueError('local/período inválido')
            if not (math.isfinite(pending['gain']) and pending['gain']>=0 and math.isfinite(context['utc'])):
                raise ValueError('recompensa/instante inválido')
        except (KeyError,TypeError,AssertionError,ValueError) as exc:
            raise SaveError('Contexto da fisgada inválido; save preservado.') from exc
    if state['rng_state'] is not None:
        def tuples(v):return tuple(tuples(x) for x in v) if isinstance(v,(list,tuple)) else v
        try:random.Random().setstate(tuples(state['rng_state']))
        except (TypeError,ValueError,OverflowError) as exc:raise SaveError('Estado aleatório inválido; save preservado.') from exc


class SaveStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = open(self.path.with_suffix(self.path.suffix+'.lock'), 'a+b')
        try:
            self.lock.seek(0)
            if not self.lock.read(1):
                self.lock.write(b'0'); self.lock.flush()
            self.lock.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.lock.close(); self.lock = None
            raise SaveError('Este perfil já está aberto em outra instância do Pesca Idle.') from exc
        self.last_good = None

    def load(self, defaults, now=None):
        now = time.time() if now is None else now
        try:
            raw_bytes = self.path.read_bytes() if self.path.exists() else None
            raw = json.loads(raw_bytes.decode('utf-8-sig')) if raw_bytes else {}
            if raw_bytes == b'':
                raise ValueError('arquivo vazio')
            state = migrate(raw, defaults, now)
            if raw_bytes and raw.get('schema_version', 1) < SCHEMA:
                backup = self.path.with_name(self.path.stem+'.pre-expansao-v1.json')
                if backup.exists() and backup.read_bytes() != raw_bytes:
                    backup = self.path.with_name(self.path.stem+'.pre-expansao-'+uuid.uuid4().hex+'.json')
                if not backup.exists():
                    with open(backup, 'xb') as file:
                        file.write(raw_bytes); file.flush(); os.fsync(file.fileno())
                self.save(state)
            self.last_good = copy.deepcopy(state)
            return state
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise SaveError(f'Não foi possível ler/migrar o save. Original preservado: {exc}') from exc

    def save(self, state):
        validate_state(state)
        payload = copy.deepcopy(state)
        payload.pop('inventario', None)  # Display-only legacy projection.
        payload['ultimo_salvo'] = time.time()
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                    dir=self.path.parent, prefix=self.path.name+'.', suffix='.tmp', delete=False) as file:
                temp = Path(file.name)
                json.dump(payload, file, ensure_ascii=False, indent=2, allow_nan=False)
                file.flush(); os.fsync(file.fileno())
            os.replace(temp, self.path)
            state['ultimo_salvo'] = payload['ultimo_salvo']
            state['inventario'] = legacy_view(state)
            self.last_good = copy.deepcopy(state)
        except (OSError, ValueError, TypeError) as exc:
            raise SaveError(f'Gravação não confirmada; o save anterior foi preservado: {exc}') from exc
        finally:
            if temp is not None and temp.exists():
                try:temp.unlink()
                except OSError:pass  # Never hide the original save failure.

    def close(self):
        if self.lock is not None:
            self.lock.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
            self.lock.close(); self.lock = None
