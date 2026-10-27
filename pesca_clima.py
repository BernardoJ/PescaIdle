"""Versioned daily weather and approved affinities; no fishing RNG or save I/O."""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from functools import lru_cache

ASSETS=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'assets'
DATA=json.loads((ASSETS/'clima_especies.json').read_text(encoding='utf-8'))
VERSION=DATA['version']
CLIMAS={row['id']:row for row in DATA['climates']}
IDS=('chuva','sol_forte','neve','ventania','ameno')  # frozen calendar order v1
if VERSION!=1 or set(CLIMAS)!=set(IDS) or any(row['weight']!=1 for row in CLIMAS.values()):
    raise ValueError('Calendário climático v1 requer os cinco climas equiprováveis.')
LEGADO='legado'
RULES={}
for group in DATA['groups']:
    for map_id in group['maps']:
        for species_id in group['species']:
            for weather,value in group['factors'].items():
                key=map_id,species_id,weather
                if key in RULES or weather not in CLIMAS or type(value) is not int or not 0<value<=200:
                    raise ValueError('Afinidade climática inválida ou duplicada.')
                if set(group['sources'])-DATA['sources'].keys():raise ValueError('Fonte climática ausente.')
                RULES[key]=(value,group)


def new_climate(profile_id,now):
    return dict(version=VERSION,seed=hashlib.sha256(('weather-v1|'+profile_id).encode()).hexdigest(),
                active_since_utc=now)


def validate_climate(record):
    if not isinstance(record,dict) or set(record)!={'version','seed','active_since_utc'}:
        raise ValueError('Estrutura de clima inválida.')
    if type(record['version']) is not int or record['version']!=VERSION:
        raise ValueError('Versão climática não suportada; dados preservados.')
    seed=record['seed']
    if not isinstance(seed,str) or len(seed)!=64 or any(c not in '0123456789abcdef' for c in seed):
        raise ValueError('Semente climática inválida.')
    utc=record['active_since_utc']
    if type(utc) not in (float,int) or not math.isfinite(utc):raise ValueError('Início climático inválido.')
    try:datetime.fromtimestamp(utc,timezone.utc)
    except (ValueError,OverflowError,OSError) as exc:raise ValueError('Início climático fora do calendário suportado.') from exc


@lru_cache(maxsize=256)
def daily_id(seed,date):
    """Stable calendar: same profile/date on every map, restart and replay."""
    date=datetime.strptime(date,'%Y-%m-%d').date().isoformat()
    value=int.from_bytes(hashlib.sha256(('weather-v1|'+seed+'|'+date).encode()).digest(),'big')
    return IDS[value%len(IDS)]


def context(state,utc,offset):
    record=state.get('clima')
    local=datetime.fromtimestamp(utc,timezone(timedelta(seconds=offset)))
    next_day=(local+timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
    legacy=record is None or utc<record['active_since_utc']
    id_=LEGADO if legacy else daily_id(record['seed'],local.date().isoformat())
    return dict(id=id_,version=0 if legacy else VERSION,data=local.date().isoformat(),
                rotulo='Regras anteriores' if legacy else CLIMAS[id_]['name'],proxima_utc=next_day.timestamp())


def validate_context(value,utc,offset):
    try:_validate_context(value,utc,offset)
    except (OverflowError,OSError) as exc:raise ValueError('Instante climático fora do calendário suportado.') from exc


def _validate_context(value,utc,offset):
    if not isinstance(value,dict):raise ValueError('Contexto climático inválido.')
    if set(value)!={'id','version','data','rotulo','proxima_utc'}:raise ValueError('Campos climáticos inválidos.')
    id_=value.get('id');version=value.get('version')
    if id_ not in (*IDS,LEGADO) or type(version) is not int or version!=(0 if id_==LEGADO else VERSION):
        raise ValueError('ID/versão do contexto climático inválidos.')
    if value['rotulo']!=('Regras anteriores' if id_==LEGADO else CLIMAS[id_]['name']):raise ValueError('Rótulo climático inválido.')
    day=datetime.fromtimestamp(utc,timezone(timedelta(seconds=offset))).date().isoformat()
    if value.get('data')!=day:raise ValueError('Data climática não corresponde à fisgada.')
    if type(value.get('proxima_utc')) not in (float,int) or not math.isfinite(value['proxima_utc']) or value['proxima_utc']<=utc:
        raise ValueError('Virada climática inválida.')
    expected=(datetime.fromtimestamp(utc,timezone(timedelta(seconds=offset)))+timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()
    if value['proxima_utc']!=expected:raise ValueError('Fim do dia climático inválido.')


def factor(map_id,species_id,weather,period_id=None):
    if weather not in (*IDS,LEGADO):raise ValueError('Clima desconhecido.')
    rule=RULES.get((map_id,species_id,weather))
    if not rule:return 1.0
    value,group=rule
    if period_id is not None and period_id not in group.get('periods',[period_id]):return 1.0
    return value/100


def affinities(weather,map_id=None,period_id=None):
    if weather not in (*IDS,LEGADO):raise ValueError('Clima desconhecido.')
    result=[]
    for (where,species,climate),(value,group) in RULES.items():
        if climate!=weather or map_id is not None and where!=map_id:continue
        result.append(dict(map_id=where,species_id=species,percent=value-100,
            active=factor(where,species,weather,period_id)!=1,periods=group.get('periods'),
            experimental=weather in group['experimental_climates'],reason=group['reason'],sources=group['sources']))
    return result


def species_affinities(species_id):
    from pesca_catalogo import LOCAIS
    parts=[]
    for weather,row in CLIMAS.items():
        for aff in affinities(weather):
            if aff['species_id']==species_id:
                suffix=' (com luz ou crepúsculo)' if aff['periods'] else ''
                parts.append(f"{row['name']}: {aff['percent']:+d}% em {LOCAIS[aff['map_id']]['nome']}"+suffix)
    return '\n'.join(parts) or 'Afinidade neutra em todos os climas.'
