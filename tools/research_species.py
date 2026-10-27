"""Development-only, read-only taxonomic lookup against the public GBIF API."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.parse
import urllib.request
from build_expansion_catalog import NEW


def research(item):
    name,fields=item; scientific=fields[0]
    url='https://api.gbif.org/v1/species/match?'+urllib.parse.urlencode({'name':scientific,'kingdom':'Animalia','strict':'true'})
    with urllib.request.urlopen(url,timeout=30) as response:
        data=json.load(response)
    valid=data.get('rank')=='SPECIES' and data.get('matchType')=='EXACT' and data.get('family')
    return name,{'status':'verificado' if valid else 'pendente','chosen_taxon':scientific,
                 'matched_name':data.get('scientificName'),'family':data.get('family') if valid else None,
                 'gbif_key':data.get('usageKey'),'accepted_key':data.get('acceptedUsageKey'),
                 'url':url,'title':'GBIF Taxonomic Backbone — '+scientific,
                 'consulted_utc':datetime.now(timezone.utc).isoformat(),
                 'claim':'Nome científico e família taxonômica; não certifica horário ou distribuição fictícia.',
                 'response':data}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    with ThreadPoolExecutor(max_workers=6) as pool:
        results=dict(pool.map(research,NEW.items()))
    args.out.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'entries':len(results),'verified':sum(s['status']=='verificado' for s in results.values()),
                      'pending':[n for n,s in results.items() if s['status']!='verificado']},ensure_ascii=False))
