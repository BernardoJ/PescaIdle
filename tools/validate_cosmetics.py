"""Regression checks for hat mounts, mascot occlusion and emissive accessories.

Uses only synthetic profiles; output defaults to the temporary profile directory.
Optional PESCA_IDLE_QA_DIR redirects the report to a dedicated QA directory.
"""
import copy
import json
import os
from pathlib import Path
import random
import sys
import tempfile
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))


def validate(profile, out):
    os.environ["PESCA_IDLE_SAVE_PATH"] = str(profile / "save.json")
    os.environ["APPDATA"] = str(profile / "appdata")
    os.environ["LOCALAPPDATA"] = str(profile / "localappdata")
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtWidgets import QApplication
    import pesca_idle as game
    from pesca_ui import configure_app
    from pesca_visual import HAT_ANCHORS, HEADBAND_X, HEADBAND_Y, PET_X, PET_Y

    app = QApplication([])
    configure_app(app)
    window = game.JogoPesca()
    window.relogio.stop(); window.timer_save.stop()
    assert game.SAVE_PATH.resolve() == (profile / "save.json").resolve()
    r = window._render
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append(name)
    hat_ids = set(r.hats) & set(r.cosmetics)
    check("Explicit mount for every hat", set(HAT_ANCHORS) == hat_ids)
    enclosed = {"chapeu_ninja", "chapeu_samurai", "chapeu_astronauta", "chapeu_raposa"}
    bare = r.character("roupa_vermelha", "chapeu_nenhum", 0)
    for hat in sorted(hat_ids):
        sprite = r.cosmetics[hat]
        ax, ay = HAT_ANCHORS[hat]
        x, y = HEADBAND_X-ax, HEADBAND_Y-ay
        check("No sprite clipping: "+hat, x >= 0 and y >= 0 and x+sprite.width() <= 32 and y+sprite.height() <= 56)
        check("Hairline contacts actual hat pixels: "+hat, any(sprite.pixelColor(xx, yy).alpha()
              for yy in range(max(0,ay-1), min(sprite.height(),ay+2))
              for xx in range(max(0,ax-1), min(sprite.width(),ax+2))))
        head = r.character("roupa_vermelha", hat, 0).copy(0,0,32,33)
        for pose in (1,2):
            check(f"Hat remains anchored in pose {pose}: {hat}", r.character("roupa_vermelha",hat,pose).copy(0,0,32,33) == head)
        if hat not in enclosed:
            check("Brim preserves eyes: "+hat, r.character("roupa_vermelha",hat,0).pixelColor(17,28) == bare.pixelColor(17,28))
    # Disable passing butterflies only for the exact pixel occlusion assertion.
    # All boat posts, basket, rail, light tint and pet animation remain real.
    pet_checks = 0
    with patch.object(r.environment, "events", return_value=None):
        for hour in (12,22):
            window._preview_clock=datetime(2026,10,6,hour)
            light=r.lighting.at(window._preview_clock)
            for level in range(11):
                window.estado["barco"]=level
                for pet in r.pets:
                    for phase in (0,2,3.1,5.3):
                        window.fase=phase
                        window.previa={"boneco":pet}
                        scene,dy=window.desenhar_cena()
                        expected=r.pet(pet,r.pet_frame(phase))
                        r.lighting.actors(expected,light)
                        visible=total=0
                        for yy in range(24):
                            for xx in range(24):
                                color=expected.pixelColor(xx,yy)
                                if color.alpha():
                                    total+=1
                                    actual=scene.pixelColor(PET_X+xx,PET_Y+dy+yy)
                                    visible+=actual.rgb()==color.rgb()
                        check(f"Whole mascot visible: {pet} boat={level} hour={hour} phase={phase}", total>0 and visible==total)
                        pet_checks+=1
    window.estado=copy.deepcopy(game.ESTADO_PADRAO)
    effect_metrics={}
    for hour in (12,22):
        window._preview_clock=datetime(2026,10,6,hour)
        for pose in (0,1,2):
            window.fisgando=1 if pose==1 else 0
            window.capturando=.6 if pose==2 else 0
            window.fase=1.3
            window.previa={"acessorio":"acessorio_nenhum"}
            base,_=window.desenhar_cena()
            for item in ("anel_verde_esmeralda","aura_cyber","escudo_bolhas"):
                window.previa={"acessorio":item}
                scene,_=window.desenhar_cena()
                difference=sum(scene.pixel(x,y)!=base.pixel(x,y) for y in range(55,120) for x in range(87,151))
                check(f"Aura visible: {item} hour={hour} pose={pose}", difference>=150)
                effect_metrics[f"{item}/{hour}/{pose}"]=difference
    window.fisgando=window.capturando=0
    def effect_image(item,phase):
        img=QImage(256,144,QImage.Format_ARGB32_Premultiplied);img.fill(Qt.transparent)
        painter=QPainter(img)
        r.accessory_effects(painter,item,phase,0,True)
        r.accessory_effects(painter,item,phase,0,False)
        painter.end();return img
    for item in ("anel_verde_esmeralda","aura_cyber","escudo_bolhas","chama_yokai"):
        check("Emissive animation: "+item,effect_image(item,0)!=effect_image(item,1.3))
    for phase,active in ((0,True),(.54,True),(.6,False),(.8,True),(.95,False),(2,False),(3.3,True)):
        check(f"Lightning schedule {phase}",r.lightning_active(phase)==active)
        image=effect_image("martelo_pesado",phase)
        sky=sum(image.pixelColor(x,y).alpha()>0 for y in range(10,65) for x in range(150,198))
        check(f"Lightning actually drawn from sky {phase}",sky>100 if active else sky==0)
    check("Lightning downtime below 2.3 seconds", all(any(r.lightning_active(i/100)
          for i in range(start,start+230)) for start in range(320)))
    for item in ("anel_verde_esmeralda","aura_cyber","escudo_bolhas","martelo_pesado","chama_yokai"):
        check("Store thumbnail available: "+item,not r.item_image("acessorio",item).isNull())
    state=copy.deepcopy(window.estado);rng=random.getstate()
    for item in ("anel_verde_esmeralda","aura_cyber","escudo_bolhas","martelo_pesado","chama_yokai"):
        window.previa={"acessorio":item}
        for phase in (.3,.8,2,3.3):
            window.fase=phase;window.desenhar_cena()
    check("Visuals leave save state unchanged",window.estado==state)
    check("Visuals preserve fishing RNG",random.getstate()==rng)
    check("Cache remains bounded",len(r.cache)<=r.CACHE_LIMIT)
    window.previa={};window.close()
    report={"count":len(checks),"checks":checks,"hat_count":len(hat_ids),
            "mascot_compositions":pet_checks,"aura_changed_pixels":effect_metrics,
            "profile_isolated":True,"backend":os.environ["QT_QPA_PLATFORM"]}
    out.mkdir(parents=True,exist_ok=True)
    (out/"cosmetics-validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="checks"},ensure_ascii=False))


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="pesca-cosmetic-qa-") as tmp:
        profile=Path(tmp)
        validate(profile,Path(os.environ.get("PESCA_IDLE_QA_DIR",str(profile/"report"))))
