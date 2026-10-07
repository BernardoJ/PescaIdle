"""Prepare imagegen masters as production pixels and map-specific masks.

All geometry is authored per scene, not inferred with the Enseada cabin rules.
Pillow is a development dependency; no code here runs in the shipped game.
"""
import argparse
import json
from pathlib import Path
import shutil
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
GEOMETRY={
 'rio_das_vitorias': {'water':[(130,48),(176,48),(225,68),(242,94),(230,144),(52,144),(37,118),(3,93),(3,72),(87,52)],'front':[(0,108,44,144),(226,116,256,144)],'horizon':48,'lights':[]},
 'mangue_das_raizes':{'water':[(131,57),(176,58),(235,85),(256,91),(256,144),(0,144),(0,96),(42,86),(64,69),(104,63)],'front':[],'horizon':57,'lights':[]},
 'pier_da_brisa':{'water':[(63,51),(256,51),(256,113),(238,132),(20,132),(0,113),(0,95),(54,88)],'front':[(0,119,20,144),(240,122,256,144)],'horizon':51,'lights':[(26,37)]},
 'recife_das_cores':{'water':[(30,35),(232,35),(256,52),(256,90),(214,127),(187,144),(76,144),(40,126),(0,90),(0,53)],'front':[(0,117,42,144),(228,113,256,144)],'horizon':35,'lights':[]},
 'mar_dos_ventos':{'water':[(0,69),(256,69),(256,144),(0,144)],'front':[],'horizon':69,'lights':[]},
 'mar_das_auroras':{'water':[(35,61),(225,61),(256,78),(256,144),(0,144),(0,80)],'front':[],'horizon':61,'lights':[]},
 'fossa_das_lanternas':{'water':[(57,46),(256,46),(256,93),(234,126),(210,144),(67,144),(39,120),(57,83)],'front':[(0,121,32,144),(233,116,256,144)],'horizon':46,'lights':[(29,5),(51,44),(55,61)]},
}


def prepare(records):
    masters=ROOT/'assets/source/mapas';masters.mkdir(parents=True,exist_ok=True)
    production=ROOT/'assets/mapas';production.mkdir(parents=True,exist_ok=True)
    manifest={}
    for record in records:
        id_=record['id'];geo=GEOMETRY[id_]
        master=masters/(id_+'.png')
        if not master.exists():shutil.copyfile(record['source'],master)
        scene=Image.open(master).convert('RGB').resize((256,144),Image.Resampling.BOX)
        scene=scene.quantize(colors=80,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGBA')
        scene.save(production/(id_+'.png'))
        water=Image.new('L',scene.size);ImageDraw.Draw(water).polygon(geo['water'],fill=255)
        # Sky palette uses only explicitly bounded sky pixels. Organic silhouettes
        # are excluded by saturation/hue classification within this scene's bounds.
        sky=Image.new('L',scene.size)
        for y in range(geo['horizon']):
            for x in range(256):
                r,g,b,a=scene.getpixel((x,y))
                if (r>g*1.04 and r>b*.95 and r>100) or (b>r and b>g*1.08 and r>100):
                    sky.putpixel((x,y),255)
        front=Image.new('RGBA',scene.size)
        for box in geo['front']:
            # Water inside the rectangle remains open; only the authored bank is foreground.
            mask=Image.new('L',scene.size);ImageDraw.Draw(mask).rectangle(box,fill=255)
            for y in range(box[1],min(144,box[3])):
                for x in range(box[0],min(256,box[2])):
                    if not water.getpixel((x,y)):front.putpixel((x,y),scene.getpixel((x,y)))
        materials=Image.new('RGB',scene.size)
        for y in range(144):
            for x in range(256):
                materials.putpixel((x,y),(255,0,0) if water.getpixel((x,y)) else
                                   (0,255,0) if sky.getpixel((x,y)) else (0,0,0))
        front.save(production/(id_+'-margem.png'))
        water.save(production/(id_+'-agua.png'));sky.save(production/(id_+'-ceu.png'))
        materials.save(production/(id_+'-materiais.png'))
        manifest[id_]={'lights':geo['lights'],'horizon':geo['horizon'],
                       'foreground_empty':not bool(front.getbbox())}
    (production/'manifesto.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (masters/'prompts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(manifest)} distinct imagegen scenes prepared with masks at 256x144.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--records',type=Path,required=True)
    args=parser.parse_args();prepare(json.loads(args.records.read_text(encoding='utf-8')))
