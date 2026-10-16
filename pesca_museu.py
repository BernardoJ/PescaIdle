"""Discovery-based exhibit references. No economy, fishing or random draws."""
import copy
from pesca_catalogo import ESPECIES

CAPACIDADE = 3


def empty_museum():
    return {'version': 1, 'aquario': [None]*CAPACIDADE}


def validate_museum(museum):
    if not isinstance(museum, dict) or type(museum.get('version')) is not int or museum['version'] != 1:
        raise ValueError('Estrutura/versão do museu inválida.')
    slots = museum.get('aquario')
    if not isinstance(slots, list) or len(slots) != CAPACIDADE:
        raise ValueError('O aquário deve guardar exatamente três espaços.')
    ids = [id_ for id_ in slots if id_ is not None]
    if any(not isinstance(id_, str) or not id_.strip() for id_ in ids):
        raise ValueError('Referência inválida no aquário.')
    if len(set(ids)) != len(ids):
        raise ValueError('Uma espécie não pode ocupar dois espaços.')
    # Unknown IDs are preserved, but never rendered as an eligible fish.


def eligible_species(state, catalogue=None):
    catalogue = ESPECIES if catalogue is None else catalogue
    counts = state.get('inventario_por_id', {})
    return tuple(sorted((id_ for id_, s in catalogue.items()
                        if s['categoria'] == 'peixe' and counts.get(id_, 0) > 0),
                        key=lambda id_: catalogue[id_]['nome'].casefold()))


def slot_status(state, slot, catalogue=None):
    catalogue = ESPECIES if catalogue is None else catalogue
    id_ = state['museu']['aquario'][slot]
    if id_ is None:
        return 'vazio'
    if id_ not in catalogue:
        return 'referencia_desconhecida'
    if catalogue[id_]['categoria'] != 'peixe':
        return 'encontro_especial'
    if state.get('inventario_por_id', {}).get(id_, 0) < 1:
        return 'nao_descoberta'
    return 'exibida'


def change_exhibit(state, slot, species_id, catalogue=None):
    catalogue = ESPECIES if catalogue is None else catalogue
    if type(slot) is not int or not 0 <= slot < CAPACIDADE:
        raise ValueError('Espaço do aquário inválido.')
    if species_id is not None:
        if not isinstance(species_id, str) or species_id not in catalogue:
            raise ValueError('Espécie desconhecida no catálogo.')
        if catalogue[species_id]['categoria'] != 'peixe':
            raise ValueError('Encontros especiais não são exibidos neste aquário.')
        if species_id not in eligible_species(state, catalogue):
            raise ValueError('Descubra esta espécie antes de exibi-la.')
        if any(i != slot and id_ == species_id for i, id_ in enumerate(state['museu']['aquario'])):
            raise ValueError('Esta espécie já está em outro espaço.')
    candidate = copy.deepcopy(state)
    candidate['museu']['aquario'][slot] = species_id
    validate_museum(candidate['museu'])
    return candidate
