"""Render an animated strip from the actual scene renderer; synthetic only."""
import argparse,os,sys,json,copy
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out==ROOT/'qa':ap.error('Use pasta nova em qa.')
    out.mkdir(parents=True,exist_ok=False)
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(out/'save.json'),APPDATA=str(out/'appdata'),LOCALAPPDATA=str(out/'localappdata'),QT_QPA_PLATFORM='offscreen')
    sys.path.insert(0,str(ROOT))
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage,QPainter,QColor,QFont
    from pesca_idle import JogoPesca
    from pesca_ui import configure_app
    from pesca_clima import IDS,CLIMAS
    from PIL import Image
    app=QApplication([]);configure_app(app);g=JogoPesca(wall_clock=lambda:1792771200.,monotonic_clock=lambda:0)
    g.relogio.stop();g.timer_save.stop();g.pausado=True;g._preview_clock=datetime(2026,10,23,12,tzinfo=timezone(timedelta(hours=-3)))
    maps=['enseada_do_poente','recife_das_cores','mar_das_auroras','mar_dos_ventos','enseada_do_poente']
    before=copy.deepcopy(g.estado);frames=[]
    for n in range(48):
        sheet=QImage(1280,170,QImage.Format_RGB32);sheet.fill(QColor('#172d40'));p=QPainter(sheet)
        font=QFont('Segoe UI');font.setPixelSize(12);p.setFont(font);p.setPen(QColor('#f1d3a2'))
        for i,weather in enumerate(IDS):
            g._preview_weather=weather;g.estado['local_atual_id']=maps[i];g.fase=n/10
            p.drawImage(i*256,25,g._render.render(g)[0]);p.drawText(i*256+6,17,CLIMAS[weather]['name'])
        p.end();frames.append(Image.frombytes('RGBA',(1280,170),bytes(sheet.constBits()),'raw','BGRA').convert('RGB'))
    frames[0].save(out/'climas.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=False)
    g.estado['local_atual_id']=before['local_atual_id'];assert g.estado==before
    g._store.close();g._closed=True;g.close()
    (out/'summary.json').write_text(json.dumps(dict(frames=48,scenes=240,source='Renderer real; fase visual independente do relógio/pesca.',state_unchanged=True),ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
