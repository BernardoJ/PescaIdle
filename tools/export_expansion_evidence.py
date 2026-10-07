"""Assemble QA contact sheets and reports; never opens/imports the game."""
import argparse,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]


def export(qa):
    matrix=qa/'validate_expansion';dest=ROOT/'docs/visual/expansao';dest.mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/'assets/catalogo_expansao.json').read_text(encoding='utf-8'))
    periods=['amanhecer','manha','dia','meio_dia','tarde','anoitecer','noite']
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',12)
    for page in range(2):
        img=Image.new('RGB',(1792,4*174),'#172434');draw=ImageDraw.Draw(img)
        for row,m in enumerate(data['maps'][page*4:page*4+4]):
            for col,p in enumerate(periods):
                tile=Image.open(matrix/(m['id']+'-'+p+'.png')).resize((256,144),Image.Resampling.NEAREST)
                x,y=col*256,row*174;img.paste(tile,(x,y))
                draw.text((x+3,y+145),m['nome'],font=font,fill='#ffe3ac')
                draw.text((x+3,y+159),p.replace('_',' '),font=font,fill='#bbd2ce')
        img.save(dest/('mapas-'+str(page+1)+'.png'))
    for name in ('efeitos.png','chapeu_raposa.png','chapeu_samurai.png','enciclopedia.png','viajar.png','expedicao.png','janela.png'):
        shutil.copyfile(matrix/name,dest/name)
    reports=ROOT/'docs/evidencias_expansao';reports.mkdir(parents=True,exist_ok=True)
    for folder,name in (('validate_expansion','validacao-expansao.json'),('validate_cosmetics','cosmetics-validation.json'),('balance_expansion','balanceamento.json')):
        shutil.copyfile(qa/folder/name,reports/name)
    print('56 real scene renders assembled; reports and new visual references exported.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--qa',type=Path,required=True);args=parser.parse_args();export(args.qa)
