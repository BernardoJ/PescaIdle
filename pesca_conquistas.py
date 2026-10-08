"""Stable collection goals and cosmetic rewards, independent of Qt."""
from pesca_catalogo import ESPECIES, LEGADO_49, EXPANSAO_88
from pesca_loja import sold_items

RECOMPENSA_LIVRO = 'enciclopedia_viva'


def fashionista_progress(state):
    owned = set(state['cosmeticos'])
    sold = sold_items()
    missing = sorted((item[2] for item in sold if item[0] not in owned), key=str.casefold)
    return {'owned': len(sold)-len(missing), 'total': len(sold), 'missing': missing}


def definitions(state, catalogue):
    owned=set(state['cosmeticos']); inv=state['inventario_por_id']
    progress = fashionista_progress(state)
    fashionista_text = f"Cosméticos vendidos: {progress['owned']}/{progress['total']}."
    if progress['missing']:
        fashionista_text += '\nFaltam: ' + ', '.join(progress['missing'])
    return [
      ('vestir_todos','Eu escolho você!','Compre o Gorro de Rato Elétrico na loja.','chapeu_pikachu' in owned),
      ('criatura_digital','Mostre-me seu Coração Valente','Compre o Dragão Digital na loja.','boneco_agumon' in owned),
      ('rei_pesca','Rei da pesca.','Registre as 49 espécies da coleção original.',all(inv.get(id_,0)>=1 for id_ in LEGADO_49)),
      ('colecao_expansao_88','Explorador das oito águas','Registre as 88 espécies da expansão.',all(inv.get(id_,0)>=1 for id_ in EXPANSAO_88)),
      ('mestre_vara','Mestre da vara.','Coloque a vara no nível máximo.',state['vara']>=10),
      ('mestre_barco','Mestre do barco.','Coloque o barco no nível máximo.',state['barco']>=10),
      ('rei_piratas','Rei dos piratas?','Compre todos os itens de pirata na loja.',all(id_ in owned for id_,_,_,_ in catalogue if 'pirata' in id_)),
      ('fashionista','Fashionista',fashionista_text,not progress['missing']),
      ('enciclopedia_viva','Enciclopédia Viva','Libere todas as informações de todas as espécies; concede o livro flutuante.',all(inv.get(id_,0)>=10 for id_ in ESPECIES)),
    ]


def grant(state, catalogue):
    unlocked=[]
    for id_,title,_,complete in definitions(state,catalogue):
        if complete and id_ not in state['conquistas']:
            state['conquistas'].append(id_);unlocked.append(title)
    if 'enciclopedia_viva' in state['conquistas'] and RECOMPENSA_LIVRO not in state['cosmeticos']:
        state['cosmeticos'].append(RECOMPENSA_LIVRO)
    return unlocked
