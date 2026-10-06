"""Export the actual game renderer; never loads the player's save."""
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from PIL import Image
from PySide6.QtWidgets import QApplication
import pesca_idle as game
from pesca_ui import configure_app

app=QApplication([])
configure_app(app)
frames=[]
with tempfile.TemporaryDirectory(prefix='pesca-animation-') as tmp:
    game.SAVE_PATH=Path(tmp)/'save.json'
    w=game.JogoPesca()
    w.relogio.stop();w.timer_save.stop()
    w.setAttribute(game.Qt.WA_DontShowOnScreen,True);w.show()
    w.estado['equipados'].update(bandeira='bandeira_brasil',boneco='boneco_gato')
    w._preview_clock=datetime(2026,10,6,18)
    for n in range(144):
        w.fase=n/12
        w.fisgando=max(0,3.5-w.fase) if 2<=w.fase<3.5 else 0
        w.capturando=max(0,4.7-w.fase) if 3.5<=w.fase<4.7 else 0
        if n==42:
            w.mostrar_popup('Lambari  +0,1 moedas','#ffe3ac')
        if w.popup:
            w.popup[2]=7-w.fase
            if w.popup[2]<=0:
                w.popup=None
        path=Path(tmp)/f'{n}.png'
        w.grab().save(str(path))
        frames.append(Image.open(path).convert('RGB'))
    output=root/'docs'/'visual'/'animacao.gif'
    durations=[80 if n%3<2 else 90 for n in range(144)]
    frames[0].save(output,save_all=True,append_images=frames[1:],duration=durations,loop=0)
    # A second clip shows gentle daytime birds/butterflies, pets and cloth.
    ambient=[]
    w.popup=None;w.fisgando=0;w.capturando=0
    w._preview_clock=datetime(2026,10,6,12)
    for n in range(144):
        w.fase=n/12
        path=Path(tmp)/f'ambient-{n}.png'
        w.grab().save(str(path))
        ambient.append(Image.open(path).convert('RGB'))
    ambient[0].save(root/'docs/visual/ambiente.gif',save_all=True,
                    append_images=ambient[1:],duration=durations,loop=0)
    night=[];cycle=[]
    for n in range(144):
        w.fase=n/12;w._preview_clock=datetime(2026,10,6,22)
        path=Path(tmp)/f'night-{n}.png';w.grab().save(str(path))
        night.append(Image.open(path).convert('RGB'))
        # QA timelapse only: actual play follows the device clock, in real time.
        w._preview_clock=datetime(2026,10,6)+timedelta(hours=24*n/143)
        path=Path(tmp)/f'cycle-{n}.png';w.grab().save(str(path))
        cycle.append(Image.open(path).convert('RGB'))
    night[0].save(root/'docs/visual/noite-animada.gif',save_all=True,
                  append_images=night[1:],duration=durations,loop=0)
    cycle[0].save(root/'docs/visual/ciclo-dia-noite.gif',save_all=True,
                  append_images=cycle[1:],duration=durations,loop=0)
    w.close()
print('Fishing, day, night and clock timelapse GIFs exported to docs/visual/')
