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
import re
from pesca_catalogo import ALIASES, ESPECIES, desbloquear, legacy_view
from pesca_tempo import snapshot
from pesca_loja import CAT, SLOTS
from pesca_moedas import set_balance, set_cents, cents
from pesca_museu import empty_museum, validate_museum
from pesca_tamanhos import ensure_sizes, validate_sizes
from pesca_piloto import validate_profile_path
from pesca_clima import new_climate,validate_climate,validate_context,context as weather_context

SCHEMA = 5  # daily weather on the isolated size pilot; not the rod proposal


class SaveError(RuntimeError):
    pass


def migrate(raw, defaults, now):
    if not isinstance(raw, dict):
        raise SaveError('Save inválido: era esperado um objeto JSON.')
    version = raw.get('schema_version', 1)
    if type(version) is not int or version > SCHEMA or version < 1:
        raise SaveError('Versão do save não suportada; o arquivo foi preservado.')
    if version >= 4 and raw.get('pilot_kind') != 'tamanhos-v1':
        raise SaveError('Schema 4 pertence a outro candidato ou não tem identificação; original preservado.')
    if version >= 4 and 'medidas_peixes' not in raw:
        raise SaveError('Perfil do piloto sem o campo de medidas; original preservado.')
    # Schema 5 must carry its own weather; expanded runtime defaults belong
    # to another initialization and must never repair an incomplete save.
    if version >= 5 and 'clima' not in raw:
        raise SaveError('Schema 5 sem clima; original preservado.')
    for key in ('equipados', 'inventario', 'inventario_por_id', 'registros_regionais', 'registros_por_periodo'):
        if key in raw and not isinstance(raw[key], dict):
            raise SaveError('Campo inválido: '+key+'; original preservado.')
    for key in ('inventario','inventario_por_id'):
        if key in raw and any(not isinstance(k,str) or type(n) is not int or n<0 for k,n in raw[key].items()):
            raise SaveError('Contagem inválida: '+key+'; original preservado.')
    for key in ('cosmeticos', 'conquistas', 'locais_desbloqueados'):
        if key in raw and (not isinstance(raw[key], list) or any(not isinstance(x,str) for x in raw[key])):
            raise SaveError('Lista inválida: '+key+'; original preservado.')
    state = copy.deepcopy(defaults)
    state.update(copy.deepcopy(raw))
    # Session/profile fields must never inherit the module's import timestamp
    # or another profile's identity from an expanded defaults dictionary.
    dynamic = ('perfil_id', 'ultimo_processado_utc', 'contexto_fuso', 'pesca',
               'pesca_pendente', 'rng_state', 'expedicao', 'viagem_pendente',
               'registros_regionais', 'registros_por_periodo', 'legado_sem_contexto',
               'local_atual_id', 'locais_desbloqueados', 'contador_eventos',
               'ultimo_evento_aplicado', 'pausado', 'museu', 'medidas_peixes')
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
    state.setdefault('museu', empty_museum())
    ensure_sizes(state)
    try:
        if version<5:
            # Historical absence remains neutral until migration. No weather is
            # invented for past catches, even if the old clock was ahead.
            state['clima']=new_climate(state['perfil_id'],now)
            if state['pesca_pendente'] is not None:
                ctx=state['pesca_pendente']['context']
                ctx['clima']=weather_context({},ctx['utc'],ctx['offset_seconds'])
        if version < 3:
            set_balance(state, raw.get('moedas', defaults.get('moedas', 0)))
        else:
            set_cents(state, raw['moedas_centavos'])
        if state['pesca_pendente'] is not None:
            pending = state['pesca_pendente']
            if version < 3:
                pending['gain_cents'] = cents(pending['gain'])
            pending['gain'] = pending['gain_cents'] / 100
    except (ValueError, TypeError, KeyError) as exc:
        raise SaveError('Saldo/recompensa inválidos; original preservado.') from exc
    state['schema_version'] = SCHEMA
    state['pilot_kind'] = 'tamanhos-v1'
    if not isinstance(state['inventario_por_id'], dict) or any(
            type(n) is not int or n < 0 for n in state['inventario_por_id'].values()):
        raise SaveError('Contagens inválidas; o save foi preservado.')
    desbloquear(state)
    validate_state(state)
    state['inventario'] = legacy_view(state)
    return state


def validate_state(state):
    from pesca_catalogo import LOCAIS
    from pesca_tempo import LABELS
    if state.get('schema_version')!=SCHEMA:raise SaveError('Versão do snapshot inválida.')
    if state.get('pilot_kind') != 'tamanhos-v1':raise SaveError('Perfil não pertence ao piloto de tamanhos.')
    try:
        validate_climate(state.get('clima'))
        validate_museum(state['museu'])
        validate_sizes(state)
    except (KeyError, ValueError, TypeError) as exc:
        raise SaveError('Clima/museu/medidas inválidos; original preservado: '+str(exc)) from exc
    if type(state.get('moedas_centavos')) is not int or state['moedas_centavos'] < 0:
        raise SaveError('Saldo em centésimos inválido.')
    if state.get('moedas') != state['moedas_centavos']/100:
        raise SaveError('Projeção do saldo inconsistente.')
    for key in ('moedas','ultimo_processado_utc','contexto_fuso'):
        if type(state[key]) not in (int,float) or not math.isfinite(state[key]):
            raise SaveError('Campo numérico inválido: '+key)
    if state['moedas']<0:raise SaveError('Saldo inválido; save preservado.')
    for key in ('vara','barco','pecas_vara','pecas_barco','total_pescados','contador_eventos'):
        if type(state[key]) is not int or state[key]<0:raise SaveError('Contador inválido: '+key)
    if state['vara']>10 or state['barco']>10:raise SaveError('Nível de equipamento não suportado.')
    for key in ('cosmeticos','conquistas','locais_desbloqueados'):
        if not isinstance(state[key],list) or any(not isinstance(x,str) for x in state[key]):
            raise SaveError('Lista inválida: '+key)
    owned=set(state['cosmeticos']);equipped=state['equipados']
    if not isinstance(equipped,dict) or set(equipped)!=set(SLOTS):
        raise SaveError('Equipamentos inválidos.')
    for slot,id_ in equipped.items():
        if not isinstance(id_,str) or id_ not in CAT or CAT[id_][1]!=slot or id_ not in owned:
            raise SaveError('Cosmético equipado inválido/não adquirido: '+slot)
    if state['local_atual_id'] not in LOCAIS or any(x not in LOCAIS for x in state['locais_desbloqueados']):
        raise SaveError('Local inválido.')
    if state['viagem_pendente'] is not None and state['viagem_pendente'] not in state['locais_desbloqueados']:
        raise SaveError('Viagem pendente inválida.')
    if type(state['pausado']) is not bool or not isinstance(state['perfil_id'],str) or not state['perfil_id']:
        raise SaveError('Identidade/pausa inválida.')
    def counts(data,depth=0):
        if not isinstance(data,dict) or any(not isinstance(k,str) for k in data):
            raise SaveError('Inventário/registros inválidos.')
        for value in data.values():
            if depth:counts(value,depth-1)
            elif type(value) is not int or value<0:raise SaveError('Contagem inválida.')
    for key in ('inventario_por_id','inventario_legado_desconhecido','legado_sem_contexto'):
        counts(state[key])
    counts(state['registros_regionais'],1);counts(state['registros_por_periodo'],2)
    plan=state['expedicao']
    if plan is not None:
        if not isinstance(plan,dict) or plan.get('status') not in ('agendada','cancelada','expirada','consumida') or plan.get('map_id') not in state['locais_desbloqueados']:
            raise SaveError('Expedição inválida.')
        if any(type(plan.get(k)) not in (int,float) or not math.isfinite(plan[k]) for k in ('inicio_utc','duracao')) or not 0<plan['duracao']<=14400:
            raise SaveError('Horário da expedição inválido.')
    phase=state['pesca'];pending=state['pesca_pendente']
    if not isinstance(phase,dict) or phase.get('etapa') not in ('aguardando','fisgando'):
        raise SaveError('Etapa de pesca inválida.')
    remaining=phase.get('restante')
    if remaining is not None and (type(remaining) not in (int,float) or not math.isfinite(remaining) or remaining<0):
        raise SaveError('Tempo restante inválido.')
    if (pending is not None)!=(phase['etapa']=='fisgando') or (pending is not None and (not isinstance(pending,dict) or remaining is None)):
        raise SaveError('Resultado pendente inconsistente; save preservado.')
    if pending:
        from pesca_catalogo import LOCAIS
        from pesca_tempo import LABELS
        try:
            context=pending['context']
            validate_context(context['clima'],context['utc'],context['offset_seconds'])
            if not (pending['species_id'] in ESPECIES or pending['species_id']=='bota_velha'):
                raise ValueError('espécie inválida')
            if context['map_id'] not in LOCAIS or context['periodo_id'] not in LABELS:
                raise ValueError('local/período inválido')
            if not (type(pending['gain_cents']) is int and pending['gain_cents']>=0 and pending['gain']==pending['gain_cents']/100 and math.isfinite(context['utc'])):
                raise ValueError('recompensa/instante inválido')
            if any(type(context.get(k)) is not int or not 0<=context[k]<=10 for k in ('vara','barco')):
                raise ValueError('equipamento inválido')
            prefix = state['perfil_id'] + ':'
            if (not isinstance(pending['id'], str)
                    or not pending['id'].startswith(prefix)
                    or re.fullmatch(r'[0-9]+', pending['id'][len(prefix):]) is None):
                raise ValueError('ID deve conter o perfil seguido de um contador decimal')
            counter = int(pending['id'][len(prefix):])
            if not 0 < counter <= state['contador_eventos']:
                raise ValueError('contador da fisgada fora do intervalo já criado')
        except (KeyError,TypeError,AssertionError,ValueError) as exc:
            raise SaveError('Contexto/ID da fisgada inválido; save preservado. '+str(exc)) from exc
    if state['rng_state'] is not None:
        def tuples(v):return tuple(tuples(x) for x in v) if isinstance(v,(list,tuple)) else v
        try:random.Random().setstate(tuples(state['rng_state']))
        except (TypeError,ValueError,OverflowError) as exc:raise SaveError('Estado aleatório inválido; save preservado.') from exc


class SaveStore:
    def __init__(self, path):
        try:
            self.path = validate_profile_path(path)
        except ValueError as exc:
            raise SaveError(str(exc)) from exc
        self.lock = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            lock_path = self._checked_path(self.path.with_suffix(self.path.suffix+'.lock'))
            self.lock = open(lock_path, 'a+b')
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
            if self.lock is not None:self.lock.close();self.lock=None
            raise SaveError('Não foi possível obter acesso exclusivo ao perfil. Feche outra instância ou confira a permissão da pasta.') from exc
        self.last_good = None
        self.last_bytes = None
        self.backup_path = self.path.with_suffix(self.path.suffix+'.bak')

    def _checked_path(self, path):
        # Auxiliary names belong to the same profile context as the main save.
        # Check their resolved target before any I/O: a .bak/.pre/.lock symlink
        # must not cross the active Android context or desktop candidate boundary.
        # Keep the original pathname for atomic replace semantics (replace a
        # local alias itself, never silently redirect writes to its target).
        try:
            validate_profile_path(path)
        except (ValueError, OSError, RuntimeError) as exc:
            raise SaveError('Caminho de save fora do contexto ou redirecionado; original preservado.') from exc
        return Path(path)

    def load(self, defaults, now=None):
        now = time.time() if now is None else now
        try:
            path = self._checked_path(self.path)
            raw_bytes = path.read_bytes() if path.exists() else None
            raw = json.loads(raw_bytes.decode('utf-8-sig')) if raw_bytes else {}
            if raw_bytes == b'':
                raise ValueError('arquivo vazio')
            state = migrate(raw, defaults, now)
            self.last_bytes = raw_bytes
            self.last_good = copy.deepcopy(state)
            if raw_bytes and raw.get('schema_version', 1) < SCHEMA:
                version=raw.get('schema_version',1)
                suffix='.pre-expansao-v1.json' if version==1 else '.pre-schema-'+str(version)+'.json'
                backup = self._checked_path(self.path.with_name(self.path.stem+suffix))
                if backup.exists() and backup.read_bytes() != raw_bytes:
                    backup = self._checked_path(self.path.with_name(self.path.stem+'.pre-expansao-'+uuid.uuid4().hex+'.json'))
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
        payload.pop('moedas', None)  # Never persist the float display projection.
        payload['ultimo_salvo'] = time.time()
        try:
            encoded=json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False).encode('utf-8')
            if self.last_bytes is not None:
                self._atomic_write(self.backup_path,self.last_bytes)
            self._atomic_write(self.path,encoded)
            state['ultimo_salvo'] = payload['ultimo_salvo']
            state['inventario'] = legacy_view(state)
            self.last_good = copy.deepcopy(state)
            self.last_bytes = encoded
        except (OSError, ValueError, TypeError) as exc:
            raise SaveError(f'Gravação não confirmada; o save anterior foi preservado: {exc}') from exc

    def _atomic_write(self, destination, data):
        destination = self._checked_path(destination)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb',
                    dir=self.path.parent, prefix=self.path.name+'.', suffix='.tmp', delete=False) as file:
                temp = Path(file.name)
                file.write(data)
                file.flush(); os.fsync(file.fileno())
            os.replace(temp, destination)
        finally:
            if temp is not None and temp.exists():
                try:temp.unlink()
                except OSError:pass  # Never hide the original save failure.

    def backup_available(self, defaults, now=None):
        try:
            migrate(json.loads(self._checked_path(self.backup_path).read_text(encoding='utf-8-sig')),defaults,time.time() if now is None else now)
            return True
        except (OSError,ValueError,TypeError,KeyError,SaveError):return False

    def recover(self, defaults, now=None):
        """Explicit recovery: keep rejected bytes in a new file before replacing."""
        try:
            restored=migrate(json.loads(self._checked_path(self.backup_path).read_text(encoding='utf-8-sig')),defaults,time.time() if now is None else now)
            path=self._checked_path(self.path)
            rejected=self._checked_path(self.path.with_name(self.path.stem+'.rejeitado-'+uuid.uuid4().hex+'.json'))
            if path.exists():
                with open(rejected,'xb') as file:
                    file.write(path.read_bytes());file.flush();os.fsync(file.fileno())
            self.last_bytes=None
            self.save(restored)
            return restored
        except (OSError,ValueError,TypeError,KeyError) as exc:
            raise SaveError('Recuperação não confirmada; original preservado: '+str(exc)) from exc

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

    def __enter__(self):return self

    def __exit__(self,*_):self.close()
