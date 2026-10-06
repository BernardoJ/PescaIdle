"""Create the design reference atlases, without loading a save."""
import json
import sys
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import pesca_idle as game

metadata={}
for kind,table in (('chapeus',game.HATS),('mascotes',game.BONECOS),('boias',game.BOIAS)):
    items=list(table.items())
    rows=(len(items)+2)//3
    img=Image.new('RGBA',(3*32,rows*24))
    for n,(id_,(grade,pal)) in enumerate(items):
        w=len(grade[0]);h=len(grade)
        x0=n%3*32+(32-w)//2;y0=n//3*24+(24-h)//2
        for y,row in enumerate(grade):
            for x,c in enumerate(row):
                if c in pal:
                    img.putpixel((x0+x,y0+y),pal[c]+(255,))
    img.resize((768,rows*192),Image.Resampling.NEAREST).save(root/'docs'/'visual'/('referencia-'+kind+'.png'))
    metadata[kind]=[id_ for id_,_ in items]
(root/'assets'/'cosmeticos.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(metadata)
