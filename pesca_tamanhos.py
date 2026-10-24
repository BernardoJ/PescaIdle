"""Pilot lengths in integer mm, independent stateless event randomness, no money."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

ASSETS=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'assets'
CONFIG=json.loads((ASSETS/'tamanhos_piloto.json').read_text(encoding='utf-8'))
RULES=CONFIG['species']

def cdf(x,rule):
    a,m,b=(rule[k] for k in ('min_mm','typical_mm','max_mm'))
    if x<=a:return 0.
    if x>=b:return 1.
    if x<=m:return (x-a)**2/((b-a)*(m-a))
    return 1-(b-x)**2/((b-a)*(b-m))

def quantile(u,rule):
    if not 0<=u<=1:raise ValueError('Quantil fora de [0,1].')
    a,m,b=(rule[k] for k in ('min_mm','typical_mm','max_mm'))
    if u<=(m-a)/(b-a):return a+math.sqrt(u*(b-a)*(m-a))
    return b-math.sqrt((1-u)*(b-a)*(b-m))

def rule_snapshot(id_):
    r=copy.deepcopy(RULES[id_]);r['version']=CONFIG['version']
    r['small_cut_mm']=math.floor(quantile(CONFIG['tail_probability'],r))
    r['large_cut_mm']=math.ceil(quantile(1-CONFIG['tail_probability'],r))
    return r

def band(mm,r):
    return 'diminuto' if mm<=r['small_cut_mm'] else 'excepcional' if mm>=r['large_cut_mm'] else 'habitual'

def sample(u,r):
    mm=min(r['max_mm'],max(r['min_mm'],math.floor(quantile(u,r)+.5)))
    return {'mm':mm,'band':band(mm,r),'rule':copy.deepcopy(r)}

def empty_sizes(profile_id):
    return {'version':1,'seed':hashlib.sha256(('length-v1:'+profile_id).encode()).hexdigest(),
            'quantity':0,'last_counter':0,'records':{},'small_species':[],'large_species':[]}

def ensure_sizes(state):
    if 'medidas_peixes' not in state:state['medidas_peixes']=empty_sizes(state['perfil_id'])
    return state['medidas_peixes']

def attach(state,event):
    if 'measurement' in event:return  # already frozen, including after a parameter edit
    id_=event['species_id']
    if id_ not in RULES or event['categoria']!='peixe':return
    sizes=ensure_sizes(state)
    raw=hashlib.sha256(('length-v1|'+sizes['seed']+'|'+event['id']+'|'+id_).encode()).digest()
    u=(int.from_bytes(raw[:8],'big')>>11)/(1<<53)
    event['measurement']=sample(u,rule_snapshot(id_))

def validate_measurement(item):
    if not isinstance(item,dict) or not isinstance(item.get('rule'),dict):raise ValueError('Medida inválida.')
    r=item['rule']
    if type(r.get('version')) is not int or r['version']!=1:raise ValueError('Versão de regra de tamanho não suportada.')
    keys=('min_mm','typical_mm','max_mm','small_cut_mm','large_cut_mm')
    if any(type(r.get(k)) is not int for k in keys):raise ValueError('Limites de medida inválidos.')
    if not 0<r['min_mm']<r['small_cut_mm']<r['typical_mm']<r['large_cut_mm']<r['max_mm']:
        raise ValueError('Limites de medida incoerentes.')
    if type(item.get('mm')) is not int or not r['min_mm']<=item['mm']<=r['max_mm']:
        raise ValueError('Comprimento fora da regra de origem.')
    if item.get('band')!=band(item['mm'],r):raise ValueError('Faixa incompatível com comprimento.')

def validate_sizes(state):
    s=state.get('medidas_peixes')
    if not isinstance(s,dict) or type(s.get('version')) is not int or s['version']!=1:
        raise ValueError('Versão de medidas não suportada.')
    if not isinstance(s.get('seed'),str) or len(s['seed'])!=64:raise ValueError('Semente de medidas inválida.')
    try:int(s['seed'],16)
    except ValueError as exc:raise ValueError('Semente de medidas inválida.') from exc
    for k in ('quantity','last_counter'):
        if type(s.get(k)) is not int or s[k]<0:raise ValueError('Contador de medidas inválido.')
    if s['last_counter']>state['contador_eventos']:raise ValueError('Contador futuro de medidas.')
    records=s.get('records')
    if not isinstance(records,dict):raise ValueError('Recordes inválidos.')
    total=0
    for id_,rec in records.items():
        if not isinstance(id_,str) or not isinstance(rec,dict) or type(rec.get('n')) is not int or rec['n']<1:
            raise ValueError('Recorde inválido.')
        total+=rec['n']
        if rec['n']>state['inventario_por_id'].get(id_,0):raise ValueError('Medidas excedem as capturas da espécie.')
        for k in ('menor','maior'):
            item=rec.get(k);validate_measurement(item)
            if not isinstance(item.get('event_id'),str) or not item['event_id']:
                raise ValueError('Recorde sem referência de evento.')
            if type(item.get('utc')) not in (int,float) or not math.isfinite(item['utc']):raise ValueError('Instante de recorde inválido.')
            if any(not isinstance(item.get(k),str) for k in ('map_id','periodo_id')):raise ValueError('Contexto de recorde inválido.')
        if rec['menor']['mm']>rec['maior']['mm']:raise ValueError('Menor recorde excede maior.')
    if total!=s['quantity']:raise ValueError('Quantidade de medidas inconsistente.')
    for k in ('small_species','large_species'):
        ids=s.get(k)
        if not isinstance(ids,list) or any(not isinstance(x,str) or x not in records for x in ids) or len(set(ids))!=len(ids):
            raise ValueError('Diversidade de medidas inválida.')
    pending=state.get('pesca_pendente')
    if isinstance(pending,dict) and 'measurement' in pending:
        if pending.get('categoria')!='peixe':raise ValueError('Somente peixes possuem medida no piloto.')
        validate_measurement(pending['measurement'])
    choices=state['museu'].get('exemplares',['maior']*3)
    if not isinstance(choices,list) or len(choices)!=3 or any(c not in ('maior','menor') for c in choices):
        raise ValueError('Seleção de exemplar inválida.')

def apply(state,event):
    if 'measurement' not in event:return []  # legacy/out-of-scope remains unmeasured
    m=event['measurement'];validate_measurement(m)
    s=ensure_sizes(state);counter=int(event['id'].rsplit(':',1)[1])
    if counter<=s['last_counter']:return []
    id_=event['species_id'];entry=copy.deepcopy(m)
    ctx=event['context']
    entry.update(event_id=event['id'],utc=ctx['utc'],map_id=ctx['map_id'],periodo_id=ctx['periodo_id'])
    rec=s['records'].get(id_);news=[]
    if rec is None:
        rec={'n':0,'menor':copy.deepcopy(entry),'maior':copy.deepcopy(entry)}
        s['records'][id_]=rec;news=['primeira']
    else:
        if m['mm']<rec['menor']['mm']:rec['menor']=copy.deepcopy(entry);news.append('menor')
        if m['mm']>rec['maior']['mm']:rec['maior']=copy.deepcopy(entry);news.append('maior')
    rec['n']+=1;s['quantity']+=1;s['last_counter']=counter
    key='small_species' if m['band']=='diminuto' else 'large_species' if m['band']=='excepcional' else None
    if key and id_ not in s[key]:s[key].append(id_);s[key].sort()
    return news

def definitions(state):
    s=ensure_sizes(state);goal=CONFIG['diversity_goal']
    return [('med_primeira','Uma fita, muitas histórias','Registre a primeira captura medida.',s['quantity']>=1),
            ('med_diminuto','Pequeno notável','Registre um exemplar diminuto.',bool(s['small_species'])),
            ('med_excepcional','Grande encontro','Registre um exemplar excepcional.',bool(s['large_species'])),
            ('med_div_pequenos','Pequena coleção',f'Registre diminutos de {goal} espécies do piloto ({len(s["small_species"])}/{goal}).',len(s['small_species'])>=goal),
            ('med_div_grandes','Grandes lembranças',f'Registre excepcionais de {goal} espécies do piloto ({len(s["large_species"])}/{goal}).',len(s['large_species'])>=goal)]

def fmt(mm):
    return (f'{mm//10}' if mm%10==0 else f'{mm//10},{mm%10}')+' cm'

def visual_scale(mm,rule):
    v=CONFIG['visual'];a,m,b=(rule[k] for k in ('min_mm','typical_mm','max_mm'))
    if mm<=m:return v['minimum']+(v['typical']-v['minimum'])*max(0,min(1,(mm-a)/(m-a)))
    return v['typical']+(v['maximum']-v['typical'])*max(0,min(1,(mm-m)/(b-m)))

def exhibit(state,slot):
    id_=state['museu']['aquario'][slot]
    rec=state.get('medidas_peixes',{}).get('records',{}).get(id_)
    if not rec:return None
    item=copy.deepcopy(rec[state['museu'].get('exemplares',['maior']*3)[slot]])
    item['visual_rule']=rule_snapshot(id_) if id_ in RULES else rec['maior']['rule']
    return item

def record_text(state,id_):
    rec=state.get('medidas_peixes',{}).get('records',{}).get(id_)
    if not rec:return 'Comprimento: sem exemplar medido. Registros antigos não recebem medidas retroativas.'
    return f"Recordes pessoais (piloto)\nMenor: {fmt(rec['menor']['mm'])}\nMaior: {fmt(rec['maior']['mm'])}\n{rec['n']} capturas medidas. Parâmetros de design provisórios."

def offline_summary(events):
    measured=[e for e in events if 'measurement' in e]
    if not measured:return ''
    changes=sum(bool(e.get('size_news')) for e in measured)
    small=sum(e['measurement']['band']=='diminuto' for e in measured)
    large=sum(e['measurement']['band']=='excepcional' for e in measured)
    return f'Medidas: {len(measured)} exemplares · {changes} novidades de recordes · {small} diminutos · {large} excepcionais. Consulte a Enciclopédia.'

for species_id in RULES:
    r=rule_snapshot(species_id)
    validate_measurement(sample(.5,r))
