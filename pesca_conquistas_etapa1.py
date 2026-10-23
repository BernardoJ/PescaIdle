"""Read-only predicates for the 24 approved goals; no RNG, money or migration."""
import json
from pathlib import Path
import sys

from pesca_museu import slot_status
from pesca_tamanhos import exhibit

ASSETS = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets'
CONFIG = json.loads((ASSETS / 'conquistas_etapa1.json').read_text(encoding='utf-8'))
GOALS = tuple(CONFIG['goals'])
SPECIES = frozenset(CONFIG['species'])
FISH = frozenset(k for k,v in CONFIG['species'].items() if v == 'peixe')
SPECIAL = SPECIES - FISH
EPIC = frozenset(CONFIG['epic_ids'])
SOLD = CONFIG['sold_slots']
DECOR = CONFIG['decorations']
MAPS = frozenset(CONFIG['map_ids'])
PERIODS = frozenset(CONFIG['period_ids'])
OCCURRENCES = tuple(CONFIG['occurrences'])
BY_MAP = {m:frozenset(o['species_id'] for o in OCCURRENCES if o['map_id']==m)
          for m in MAPS}
BY_CONTEXT = {(m,p):frozenset(o['species_id'] for o in OCCURRENCES
                             if o['map_id']==m and p in o['periods'])
              for m in MAPS for p in PERIODS}


def _count(mapping, key):
    value = mapping.get(key, 0)
    return value if type(value) is int and value > 0 else 0


def progress(state):
    """Read existing facts; never assign a location/time to contextless legacy."""
    inv = state.get('inventario_por_id', {})
    known = {id_ for id_ in SPECIES if _count(inv,id_)}
    regional = state.get('registros_regionais', {})
    regional_ids = {m:{id_ for id_ in BY_MAP[m] if _count(regional.get(m,{}),id_)}
                    for m in MAPS}
    visited = sum(bool(ids) for ids in regional_ids.values())
    periods = {p for m in MAPS for p in PERIODS if any(
        _count(state.get('registros_por_periodo',{}).get(m,{}).get(p,{}),id_)
        for id_ in BY_CONTEXT[m,p])}
    three_margins = sum(len(ids & FISH)>=3 for ids in regional_ids.values())
    slots = state.get('museu',{}).get('aquario',[None]*3)
    displayed = [i for i,id_ in enumerate(slots) if id_ in FISH
                 and slot_status(state,i)=='exibida']
    display_ids = {slots[i] for i in displayed}
    small,large = set(),set()
    for i in displayed:
        if slots[i] not in CONFIG['measured_species']:
            continue
        measured = exhibit(state,i)
        if measured:
            if measured['band']=='diminuto':small.add(slots[i])
            elif measured['band']=='excepcional':large.add(slots[i])
    contrast = len(display_ids)==3 and any(a!=b for a in small for b in large)
    decor = state.get('museu',{}).get('decoracao',{})
    bought = set(decor.get('compradas',[])) & DECOR.keys()
    areas = {DECOR[id_]['area'] for id_ in bought}
    selected = decor.get('equipadas',{})
    furnished = sum(selected.get(slot) in bought
                    and DECOR[selected[slot]]['slot']==slot for slot in CONFIG['decoration_slots'])
    paid = set(state.get('cosmeticos',[])) & SOLD.keys()
    categories = {SOLD[id_] for id_ in paid}
    outfit = state.get('equipados',{})
    ninja = sum(outfit.get(slot)==id_ and id_ in paid for slot,id_ in
                (('chapeu','chapeu_ninja'),('roupa','roupa_ninja')))
    result = {}

    def threshold(code, value, target, unit):
        result[code] = (f'{min(value,target)}/{target} {unit}', value>=target)

    threshold('C01',sum(_count(inv,id_) for id_ in FISH),25,'capturas de peixes')
    threshold('C02',len(known),10,'espécies')
    threshold('C03',len(known),25,'espécies')
    threshold('C04',sum(_count(inv,id_)>=5 for id_ in SPECIES),20,'espécies com 5 registros')
    threshold('C05',sum(_count(inv,id_)>=10 for id_ in SPECIES),20,'espécies com 10 registros')
    threshold('C07',len(known & EPIC),1,'espécie Épico')
    threshold('C09',len(known & SPECIAL),5,'encontros especiais distintos')
    threshold('C10',visited,2,'mapas com registros')
    threshold('C11',visited,len(MAPS),'mapas com registros')
    threshold('C12',len(periods),3,'períodos com registros')
    threshold('C13',len(periods),len(PERIODS),'períodos com registros')
    threshold('C15',three_margins,3,'mapas com 3 peixes distintos')
    threshold('C16',len(display_ids),1,'espécie em exposição')
    threshold('C17',len(display_ids),3,'espécies em exposição')
    result['C18'] = (f'{len(display_ids)}/3 espécies; diminuto: '+('sim' if small else 'não')+
                     '; excepcional: '+('sim' if large else 'não'), contrast)
    threshold('C19',len(bought),1,'decoração adquirida')
    threshold('C20',len(areas),2,'áreas com decoração adquirida')
    threshold('C21',furnished,len(CONFIG['decoration_slots']),'tipos decorados')
    threshold('C22',len(bought),len(DECOR),'decorações adquiridas')
    result['C23'] = (f'{min(len(paid),3)}/3 cosméticos; {min(len(categories),3)}/3 categorias',
                     len(paid)>=3 and len(categories)>=3)
    result['C24'] = (f'{min(len(paid),10)}/10 cosméticos; {min(len(categories),4)}/4 categorias',
                     len(paid)>=10 and len(categories)>=4)
    threshold('C25',ninja,2,'peças ninja em uso')
    threshold('C27',max(state['vara'],state['barco']),1,'nível em vara ou barco')
    result['C28'] = (f"Vara: {min(state['vara'],3)}/3; barco: {min(state['barco'],3)}/3",
                     state['vara']>=3 and state['barco']>=3)
    return result


def definitions(state):
    values = progress(state)
    return [(g['id'],g['title'],
             g['description']+f"\n{g['difficulty']} · {g['group']} · Progresso: {values[g['code']][0]}.",
             values[g['code']][1]) for g in GOALS]
