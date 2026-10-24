"""Render each cosmetic and equipment pair under all maps and climates."""
import argparse,copy,json,os,sys,time
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();out=args.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out==ROOT/'qa':ap.error('Use pasta nova em qa.')
    out.mkdir(parents=True,exist_ok=False)
    for name in ['tmp','appdata','localappdata']:(out/name).mkdir()
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(out/'save.json'),APPDATA=str(out/'appdata'),LOCALAPPDATA=str(out/'localappdata'),
        TEMP=str(out/'tmp'),TMP=str(out/'tmp'),QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0,str(ROOT))
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication,QEvent
    from pesca_idle import JogoPesca
    from pesca_clima import IDS
    from pesca_catalogo import LOCAIS
    from pesca_loja import CATALOGO
    from pesca_clima_ui import ClimateDialog
    from pesca_ui import configure_app
    app=QApplication([]);configure_app(app);g=JogoPesca(wall_clock=lambda:1792771200.,monotonic_clock=lambda:0.)
    g.relogio.stop();g.timer_save.stop();g.pausado=True;g.fase=14;g._preview_clock=datetime(2026,10,23,12,tzinfo=timezone(timedelta(hours=-3)))
    original=copy.deepcopy(g.estado);cosmetics=equipment=0;started=time.perf_counter()
    for mid in LOCAIS:
        g.estado['local_atual_id']=mid
        for weather in IDS:
            g._preview_weather=weather
            for id_,slot,_,_ in CATALOGO:
                g.estado['equipados']=dict(original['equipados']);g.estado['equipados'][slot]=id_
                for phase in [2.,20.]:
                    g.fase=phase;assert not g._render.render(g)[0].isNull();cosmetics+=1
            g.estado['equipados']=dict(original['equipados'])
            for rod in range(11):
                for boat in range(11):
                    g.estado['vara']=rod;g.estado['barco']=boat
                    assert not g._render.render(g)[0].isNull();equipment+=1
    g.estado=copy.deepcopy(original)
    for _ in range(50):
        dialog=ClimateDialog(g);dialog.show();app.processEvents();dialog.accept();assert not dialog.timer.isActive()
        dialog.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
    assert not g.findChildren(ClimateDialog)
    assert g.estado==original
    g._store.close();g._closed=True;g.close()
    report=dict(cosmetic_renders=cosmetics,equipment_pair_renders=equipment,maps=8,climates=5,cosmetic_items=len(CATALOGO),
        dialog_lifecycles=50,timers_stopped=True,game_state_and_rng_unchanged=True,seconds=time.perf_counter()-started,
        scope='Cada item individual em duas fases e todo par vara/barco; não enumera todas as combinações simultâneas de cosméticos.')
    (out/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
