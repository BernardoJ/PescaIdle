"""Aquarium-only catalogue and copy-on-write transactions; no fishing bonuses."""
import copy
import json
from pathlib import Path
import sys
from pesca_moedas import debit

ASSETS=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'assets'
DATA=json.loads((ASSETS/'aquario_decoracoes.json').read_text(encoding='utf-8'))
SLOTS={s['id']:s for s in DATA['slots']}
CAT={s['id']:s for s in DATA['items']}
CATALOGO=tuple(sorted(DATA['items'],key=lambda s:(s['price'],s['nome'].casefold())))


def empty_decoration():
    return dict(version=1,compradas=[],equipadas={slot:None for slot in SLOTS})


def validate_decoration(record):
    if not isinstance(record,dict) or type(record.get('version')) is not int or record['version']!=1:
        raise ValueError('Versão/estrutura de decoração inválida.')
    owned=record.get('compradas');selected=record.get('equipadas')
    if (not isinstance(owned,list) or any(not isinstance(i,str) or not i.strip() for i in owned)
            or len(set(owned))!=len(owned)):
        raise ValueError('Lista de decorações adquiridas inválida.')
    if not isinstance(selected,dict) or set(selected)!=set(SLOTS):
        raise ValueError('Espaços de decoração inválidos.')
    for slot,id_ in selected.items():
        if id_ is None:continue
        if not isinstance(id_,str) or id_ not in owned:
            raise ValueError('Decoração selecionada não adquirida.')
        if id_ in CAT and CAT[id_]['slot']!=slot:
            raise ValueError('Decoração em categoria incorreta.')
    # Unknown future IDs remain stored, but are never sold or drawn as another item.


def record(state):
    return state.get('museu',{}).get('decoracao',empty_decoration())


def selections(state,preview=None):
    selected={**record(state)['equipadas'],**(preview or {})}
    return tuple(selected.get(slot) if selected.get(slot) in CAT and CAT[selected[slot]]['slot']==slot else None
                 for slot in SLOTS)


def purchase(state,id_):
    if id_ not in CAT:raise ValueError('Decoração desconhecida.')
    candidate=copy.deepcopy(state)
    decor=candidate['museu'].setdefault('decoracao',empty_decoration())
    validate_decoration(decor)
    if id_ in decor['compradas']:raise ValueError('Esta decoração já foi comprada.')
    if not debit(candidate,CAT[id_]['price']):raise ValueError('Moedas insuficientes.')
    decor['compradas'].append(id_)
    decor['equipadas'][CAT[id_]['slot']]=id_
    validate_decoration(decor)
    return candidate


def equip(state,slot,id_):
    if slot not in SLOTS:raise ValueError('Categoria de decoração desconhecida.')
    candidate=copy.deepcopy(state)
    decor=candidate['museu'].setdefault('decoracao',empty_decoration())
    validate_decoration(decor)
    if id_ is not None:
        if id_ not in CAT or CAT[id_]['slot']!=slot:raise ValueError('Decoração incompatível.')
        if id_ not in decor['compradas']:raise ValueError('Compre esta decoração na loja.')
    decor['equipadas'][slot]=id_
    return candidate


def restore_default(state):
    candidate=copy.deepcopy(state)
    decor=candidate['museu'].setdefault('decoracao',empty_decoration())
    validate_decoration(decor)
    decor['equipadas']={slot:None for slot in SLOTS}
    return candidate
