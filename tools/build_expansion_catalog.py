"""Development-only adaptation of the exact proposal; no game imports or saves.

Legacy values come from the immutable baseline fixture. Production reads only
assets/catalogo_expansao.json, never the design fixture or this build script.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
NEW = {
 'Carpa-comum':('Cyprinus carpio',12,3,'carp'),
 'Carpa-capim':('Ctenopharyngodon idella',18,2,'carp'),
 'Acará':('Geophagus brasiliensis',10,3,'disk'),
 'Traíra':('Hoplias malabaricus',24,2,'long'),
 'Jundiá':('Rhamdia quelen',28,2,'catfish'),
 'Curimbatá':('Prochilodus lineatus',12,3,'carp'),
 'Matrinxã':('Brycon amazonicus',18,3,'carp'),
 'Piabanha':('Brycon insignis',22,3,'carp'),
 'Piraputanga':('Brycon hilarii',18,3,'carp'),
 'Piapara':('Megaleporinus obtusidens',16,3,'striped'),
 'Dourado':('Salminus brasiliensis',35,2,'long'),
 'Pintado':('Pseudoplatystoma corruscans',40,2,'catfish'),
 'Pirarara':('Phractocephalus hemioliopterus',45,2,'catfish'),
 'Jaú':('Zungaro jahu',50,2,'catfish'),
 'Tainha':('Mugil liza',6,4,'long'),
 'Carapeba':('Diapterus rhombeus',7,4,'disk'),
 'Robalo-flecha':('Centropomus undecimalis',24,3,'long'),
 'Robalo-peva':('Centropomus parallelus',18,3,'long'),
 'Parati':('Mugil curema',5,4,'long'),
 'Corvina':('Micropogonias furnieri',12,3,'long'),
 'Bagre-amarelo':('Cathorops spixii',14,3,'catfish'),
 'Peixe-rei':('Atherinella brasiliensis',3,4,'long'),
 'Peixe-agulha':('Strongylura marina',10,3,'needle'),
 'Betara':('Menticirrhus americanus',8,3,'long'),
 'Sargo':('Diplodus argenteus',6,4,'disk'),
 'Sargentinho':('Abudefduf saxatilis',3,5,'striped'),
 'Peixe-borboleta':('Chaetodon striatus',12,3,'striped'),
 'Cirurgião-patela':('Paracanthurus hepatus',15,3,'disk'),
 'Moreia-verde':('Gymnothorax funebris',24,3,'eel'),
 'Albacora-laje':('Thunnus albacares',18,4,'tuna'),
 'Peixe-voador':('Hirundichthys affinis',8,5,'flying'),
 'Dourado-do-mar':('Coryphaena hippurus',24,4,'long'),
 'Peixe-vela':('Istiophorus platypterus',60,3,'sailfish'),
 'Bacalhau-polar':('Boreogadus saida',2,5,'long'),
 'Halibute-do-atlântico':('Hippoglossus hippoglossus',12,4,'flatfish'),
 'Peixe-lobo':('Anarhichas lupus',18,3,'long'),
 'Peixe-pescador-abissal':('Melanocetus johnsonii',80,4,'angler'),
 'Peixe-víbora':('Chauliodus sloani',40,4,'fang'),
 'Enguia-pelicano':('Eurypharynx pelecanoides',60,4,'eel'),
}
MAP_IDS = ('enseada_do_poente','rio_das_vitorias','mangue_das_raizes','pier_da_brisa',
           'recife_das_cores','mar_dos_ventos','mar_das_auroras','fossa_das_lanternas')
PERIOD_IDS={'amanhecer':'amanhecer','manhã':'manha','dia':'dia','meio-dia':'meio_dia',
            'tarde':'tarde','anoitecer':'anoitecer','noite':'noite'}


def stable_initial_id(name):
    # Used ONCE in development. IDs are stored explicitly in the production file.
    return ''.join(c for c in unicodedata.normalize('NFKD',name.lower())
                   if not unicodedata.combining(c)).replace('-','_').replace(' ','_')


def legacy_shape(name):
    for text, kind in (('Baleia','whale'),('Orca','orca'),('Golfinho','dolphin'),('Vaquita','dolphin'),
                       ('Narval','narwhal'),('Tartaruga','turtle'),('Manta','ray'),('Tubarão','shark'),
                       ('Celacanto','coelacanth'),('Cavalinho','seahorse'),('Polvo','octopus'),
                       ('Lula','squid'),('Água-viva','jelly'),('Lagosta','lobster'),('Mexilhão','shell'),
                       ('Caranguejo','crab'),('Camarão','shrimp'),('Krill','shrimp'),('Calano','copepod'),
                       ('Copépode','copepod'),('Salpa','salp'),('Linguado','flatfish'),('Peixe-lua','moonfish'),
                       ('Peixe-ogro','fang'),('Peixe-mão','handfish'),('Atum','tuna'),('lanterna','lantern'),
                       ('papagaio','parrot'),('palhaço','clownfish')):
        if text in name:return kind
    return 'carp' if name in ('Lambari','Pacu','Tambaqui','Tilápia-do-nilo') else 'long'


def build(proposal_path, legacy_path, verification_path):
    proposal=json.loads(proposal_path.read_text(encoding='utf-8'))
    source=ast.parse(legacy_path.read_text(encoding='utf-8-sig'))
    literals={node.targets[0].id:ast.literal_eval(node.value) for node in source.body
              if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
              and node.targets[0].id in ('LOOT','CURIOSIDADES')}
    legacy={s['nome']:s for s in literals['LOOT'] if s['tipo']=='peixe'}
    verification=json.loads(verification_path.read_text(encoding='utf-8')) if verification_path.exists() else {}
    names={s['nome']:s for group in ('catalogos_peixes','encontros_especiais')
           for rows in proposal[group].values() for s in rows}
    assert {n for n,s in names.items() if s['novo']}==set(NEW)
    assert {n for n,s in names.items() if not s['novo']} <= set(legacy)
    specials={s['nome'] for rows in proposal['encontros_especiais'].values() for s in rows}
    species=[]
    for i,name in enumerate([*legacy,*[n for n in names if n not in legacy]]):
        old=legacy.get(name)
        if old:
            value,weight,shape=old['valor'],old['peso'],legacy_shape(name)
            scientific=old['cientifico'];fact=literals['CURIOSIDADES'][name]
            rarity=('Comum' if weight>=8 else 'Incomum' if weight>=3 else 'Raro' if weight>=.5
                    else 'Épico' if weight>=.1 else 'Lendário')
            bonus=value>=25;verified={'status':'legado_preservado'}
        else:
            scientific,value,weight,shape=NEW[name]
            rarity='Incomum' if weight>=3 else 'Raro';bonus=rarity=='Raro'
            verified=verification.get(name,{'status':'pendente'})
            family=verified.get('family')
            fact=(f'Na classificação taxonômica verificada, pertence à família {family}.'
                  if family else 'Identificação científica em pesquisa; horários e locais são convenções do jogo.')
        digest=hashlib.sha256(name.encode()).digest()
        species.append({'id':stable_initial_id(name),'nome':name,'aliases':[name],
           'cientifico':scientific,'categoria':'especial' if name in specials else 'peixe',
           'valor':value,'raridade':rarity,'rod_bonus':bonus,'curiosidade':fact,
           'verification':verified,'sprite':{'family':shape,'palette':list(digest[:3]),'variant':i}})
    ids={s['nome']:s['id'] for s in species}
    maps=[];occurrences=[]
    for id_,(name,meta) in zip(MAP_IDS,proposal['locais'].items()):
        maps.append({'id':id_,'nome':name,'nivel_barco':meta['nivel_barco_desbloqueio'],
                     'descricao':meta['direcao_visual'],'trash_probability':.04,'special_probability':.10})
        for category in ('catalogos_peixes','encontros_especiais'):
            for row in proposal[category].get(name,[]):
                s=next(s for s in species if s['nome']==row['nome'])
                weight=NEW[row['nome']][2] if row['novo'] else legacy[row['nome']]['peso']
                occurrences.append({'species_id':s['id'],'map_id':id_,
                   'periods':[PERIOD_IDS[p] for p in row['periodos']], 'weight':weight,
                   'preferences':{PERIOD_IDS[p]:1.0 for p in row['periodos']}})
    # Any genuine later species remains available in its previous initial location.
    for name in set(legacy)-set(names):
        occurrences.append({'species_id':ids[name],'map_id':MAP_IDS[0],
            'periods':list(PERIOD_IDS.values()),'weight':legacy[name]['peso'],
            'preferences':{p:1.0 for p in PERIOD_IDS.values()}})
    data={'version':1,'proposal_sha256':hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
          'species':species,'maps':maps,'occurrences':occurrences,
          'legacy_collection':[ids[n] for n,s in names.items() if not s['novo']],
          'expansion_collection':[ids[n] for n in names]}
    target=ROOT/'assets'/'catalogo_expansao.json'
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'species':len(species),'occurrences':len(occurrences),
                     'maps':len(maps),'legacy':len(data['legacy_collection'])}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal',type=Path,required=True)
    parser.add_argument('--legacy-source',type=Path,required=True)
    parser.add_argument('--verification',type=Path,required=True)
    args=parser.parse_args();build(args.proposal,args.legacy_source,args.verification)
