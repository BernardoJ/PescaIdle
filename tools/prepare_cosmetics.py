"""Production atlas extraction; runtime consumes only Qt PNGs and the ID manifest."""
import json
from pathlib import Path
from PIL import Image

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'assets/cosmeticos.json').read_text(encoding='utf-8'))
hat_sizes=[(24,12),(21,12),(17,15),(23,13),(25,13),(20,19),
           (20,15),(21,22),(20,22),(23,23),(25,14),(25,22),
           (22,23),(23,12),(22,15),(22,23),(23,16)]
for category,ids in manifest.items():
    master=Image.open(root/'assets/source'/f'{category}-original.png').convert('RGBA')
    rows=(len(ids)+2)//3
    atlas=Image.new('RGBA',(96,rows*32))
    for i,id_ in enumerate(ids):
        cx,cy=i%3,i//3
        tile=master.crop((round(cx*master.width/3),round(cy*master.height/rows),
                          round((cx+1)*master.width/3),round((cy+1)*master.height/rows)))
        bounds=tile.getchannel('A').point(lambda a:255 if a>=100 else 0).getbbox()
        assert bounds, f'Empty atlas cell: {id_}'
        tile=tile.crop(bounds)
        maxw,maxh=hat_sizes[i] if category=='chapeus' else (16,16) if category=='mascotes' else (10,11)
        factor=min(maxw/tile.width,maxh/tile.height)
        size=(max(1,round(tile.width*factor)),max(1,round(tile.height*factor)))
        tile=tile.resize(size,Image.Resampling.BOX)
        alpha=tile.getchannel('A').point(lambda a:255 if a>=100 else 0)
        tile=tile.convert('RGB').quantize(colors=24,method=Image.Quantize.MEDIANCUT,
                                         dither=Image.Dither.NONE).convert('RGBA')
        tile.putalpha(alpha)
        atlas.paste(tile,(cx*32+(32-tile.width)//2,cy*32+32-tile.height))
    atlas.save(root/'assets'/f'{category}.png')
    atlas.resize((atlas.width*6,atlas.height*6),Image.Resampling.NEAREST).save(
        root/'docs/visual'/f'itens-{category}.png')
    print(category,len(ids),atlas.size)
