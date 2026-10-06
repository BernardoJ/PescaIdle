"""Original pixel panel and inventory icons. Offline authoring only (Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parents[1]
out=root/'assets'
panel=Image.new('RGBA',(48,48),'#1b283a')
d=ImageDraw.Draw(panel)
for offset,color in ((0,'#151e2b'),(1,'#695e4f'),(2,'#e0b77b'),(3,'#f1d59d'),
                     (4,'#8c765d'),(5,'#293a4c'),(6,'#586675'),(7,'#1c2b3d')):
    d.rectangle((offset,offset,47-offset,47-offset),outline=color,width=1)
d.rectangle((8,8,39,39),fill='#233449')
for x,y in ((3,3),(44,3),(3,44),(44,44)):
    d.polygon([(x-2,y),(x,y-2),(x+2,y),(x,y+2)],fill='#f6ddb0')
    d.point((x,y),fill='#9a7851')
panel.save(out/'painel.png')

P={'k':'#25283c','b':'#586c83','B':'#94b7bc','g':'#b08b4e','G':'#f3cf82',
   'w':'#f2e5c8','r':'#be5c50','R':'#ed9a6c','s':'#5c8c71','S':'#9ac995'}
icons={
 'chapeu':["............","....gggg....","...gGGGGg...","...gGGGGg...","..gggrrrgg..",".gGGGGGGGGg.","..gggggggg.."],
 'roupa':["...rr..rr...","..rRRrrRRr..",".rRRRRRRRRr.",".rrrRRRRrrr.","...rRRRRr...","...rRRRRr...","...rrrrrr..."],
 'bandeira':["..G.........","..gRRRRRR...","..gRRRRR....","..gRRRRRR...","..gRRRRRR...","..g.........","..g.........","..g........."],
 'boia':[".....G......","....www.....","...rRRRr....","...rRRRr....","...rRRRr....","....www.....",".....b......","..BBBBBBB..."],
 'boneco':["..g.....g...","..gGGGGGg...","..GkGGGkG...","...GGGGG....","....gGg.....","..gGGGGGg...","...gGGGg....","...g...g...."],
 'acessorio':["....BBB.....","...BsSSB....","....BsB.....","....gGg.....","...g...g....","..g.....g...","..g.....g...","...ggggg...."],
 'barco':["............","..g......g..","..gGGGGGGg..",".gRRRRRRRGg.","..grrrrrgg..","...gggggg...","..BBBBBBBB.."],
 'vara':[".........G..","........G.b.",".......G..b.","......G...b.",".....g....b.","....g.....b.","...g......r.","..g.......w."],
 'loja':["....gggg....",".....gg.....","...gGGGGg...","..gGGGGGGg..","..gGGgGGGg..","..gGgggGGg..","...gGGGGg...","....gggg...."],
 'livro':[".gggg..gggg.",".gwwwggwwwg.",".gwwwwgwwwg.",".gwbwwgwbwg.",".gwwwwgwwwg.",".gwbwwgwbwg.",".gggggggggg.",".....gg....."],
 'peixe':["......BBB...","...BBBwwwB..","BB.BwwwwkBB.",".BBwwwwwwwB.","BB.BBBBBBB..","......BBB..."],
 'conquistas':[".G.gGGg.G...",".G.gGGg.G...",".GGGGGGGG...","...gGGg.....","....gg......","....GG......","...gGGg.....","..gggggg...."],
 'pausa':["..GG..GG....","..GG..GG....","..GG..GG....","..GG..GG....","..GG..GG....","..GG..GG...."],
 'sair':["..rr....rr..","...rr..rr...","....rrrr....",".....rr.....","....rrrr....","...rr..rr...","..rr....rr.."],
}
for name,rows in icons.items():
    img=Image.new('RGBA',(16,16))
    px=img.load()
    y0=(16-len(rows))//2
    for y,row in enumerate(rows):
        for x,c in enumerate(row):
            if c in P:
                # Colored lower edge and upper-right material highlight.
                px[x+2,y+y0]=tuple(bytes.fromhex(P[c][1:]))+(255,)
    img.resize((32,32),Image.Resampling.NEAREST).save(out/('icone-'+name+'.png'))
print('Original nine-slice RPG panel and 14 inventory/menu icons generated.')
