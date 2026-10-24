"""Reproducible visual capture, synthetic in-memory state; no game/save execution.

Run with --source pointing to either the fixed PR5 archive or this candidate.
Only QApplication, the actual museum widgets and their renderers are created.
Output must be a NEW directory below source/qa; personal profiles are never read.
"""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    root, out = args.source.resolve(strict=True), args.out.resolve()
    if not out.is_relative_to(root / 'qa') or out == root / 'qa':
        parser.error('Use a NEW output directory below source/qa.')
    if out.exists():
        parser.error('Output exists; choose another directory. No evidence overwritten.')
    out.mkdir(parents=True)
    profile = out / 'synthetic-profile'
    for folder in ('appdata', 'localappdata', 'tmp'):
        (profile / folder).mkdir(parents=True)
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(profile / 'save.json'),
        APPDATA=str(profile / 'appdata'), LOCALAPPDATA=str(profile / 'localappdata'),
        TEMP=str(profile / 'tmp'), TMP=str(profile / 'tmp'),
        QT_SCALE_FACTOR='1', QT_AUTO_SCREEN_SCALE_FACTOR='0')
    sys.path.insert(0, str(root))
    # The boundary is configured before ANY product or Qt imports.
    from PySide6 import __version__ as qt_binding
    from PySide6.QtCore import Qt, QRectF
    from PySide6.QtGui import QImage, QPainter, QColor, QFont
    from PySide6.QtWidgets import QApplication, QWidget
    from pesca_catalogo import ESPECIES
    from pesca_especies_visual import species_image
    from pesca_tamanhos import RULES, rule_snapshot, band
    from pesca_tamanho_visual import scale_for
    from pesca_museu_ui import AquariumView, MuseuDialog
    from pesca_ui import configure_app
    improved = (root / 'pesca_museu_visual.py').exists()
    if improved:
        from pesca_museu_visual import aquarium_species_image, ART
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    configure_app(app)
    ids = [key for key, value in ESPECIES.items() if value['categoria'] == 'peixe']
    if improved and set(ids) != set(ART['species']):
        raise ValueError('Aquarium artwork does not cover exactly the eligible catalogue.')
    old_hashes = {id_: hashlib.sha256(bytes(species_image(id_).constBits())).hexdigest()
                  for id_ in ids}
    def measurement(id_, kind):
        rule = rule_snapshot(id_)
        mm = rule['min_mm' if kind == 'menor' else 'max_mm']
        return dict(mm=mm, band=band(mm, rule), rule=rule,
                    event_id='synthetic-aquarium:'+id_+':'+kind,
                    utc=1792411200, map_id='enseada_do_poente', periodo_id='meio_dia')
    def state_for(selected, kind='maior'):
        records = {id_: dict(n=2, menor=measurement(id_, 'menor'),
                            maior=measurement(id_, 'maior')) for id_ in ids if id_ in RULES}
        return dict(inventario_por_id={id_:2 for id_ in ids},
                    museu=dict(version=1, aquario=selected,
                               exemplares=[kind]*3),
                    medidas_peixes=dict(version=1, records=records))
    class SyntheticHost(QWidget):
        def __init__(self, state):
            super().__init__()
            self.estado = state
        def _commit(self, _):
            raise RuntimeError('Visual capture never persists or changes the fixture.')
    def image(id_, detail=2):
        return aquarium_species_image(id_, detail) if improved else species_image(id_)
    def save(img, name):
        if not img.save(str(out / name)):
            raise OSError('PNG write failed: '+name)
    def label(p, x, y, text, size=10, color='#dce6dc', bold=False):
        p.setPen(QColor(color));p.setFont(QFont('Segoe UI', size, QFont.Bold if bold else QFont.Normal))
        p.drawText(x, y, text)
    # Pranchas are labelled as artwork, distinct from actual GUI captures.
    for page in range(4):
        subset = ids[page*17:(page+1)*17]
        canvas = QImage(1140, 760, QImage.Format_ARGB32_Premultiplied)
        canvas.fill(QColor('#182c39'));p = QPainter(canvas)
        label(p, 24, 28, args.label+' | Prancha de sprites '+str(page+1)+'/4', 14, bold=True)
        for n,id_ in enumerate(subset):
            x,y=24+(n%3)*374,52+(n//3)*114
            p.fillRect(x,y,354,104,QColor('#234854'))
            p.drawImage(QRectF(x+8,y+6,144,96),image(id_))
            label(p,x+164,y+34,ESPECIES[id_]['nome'],9,bold=True)
            # Scientific names can be long; smaller type and two lines, no truncation.
            genus, species = ESPECIES[id_]['cientifico'].split(' ',1)
            label(p,x+164,y+55,genus,9);label(p,x+164,y+72,species,9)
        p.end();save(canvas,f'catalogo-{page+1}.png')
    selected=['lambari','tilapia_do_nilo','carpa_comum','traira']
    canvas=QImage(1200,640,QImage.Format_ARGB32_Premultiplied);canvas.fill(QColor('#182c39'))
    p=QPainter(canvas);label(p,24,30,args.label+' | Quatro espécies iniciais',16,bold=True)
    from pesca_tamanho_visual import draw_fish
    if improved:
        from pesca_museu_visual import draw_aquarium_fish
    for row,id_ in enumerate(selected):
        y=54+row*140;p.fillRect(20,y,1160,130,QColor('#234854'))
        label(p,36,y+28,ESPECIES[id_]['nome'],13,bold=True)
        label(p,36,y+51,ESPECIES[id_]['cientifico'],10)
        for j,kind in enumerate(('menor','maior')):
            p.save();p.translate(580+j*340,y+63);p.scale(4,4)
            if improved:draw_aquarium_fish(p,id_,0,0,measurement(id_,kind),detail=2)
            else:draw_fish(p,id_,0,0,measurement(id_,kind))
            p.restore();label(p,490+j*340,y+119,kind.title()+' | escala '+str(round(scale_for(measurement(id_,kind),id_),2)),10)
    p.end();save(canvas,'quatro-especies.png')
    scenes={
        'iniciais':['lambari','tilapia_do_nilo','carpa_comum'],
        'rio':['traira','pintado','pirarara'],
        'recife':['peixe_palhaco','cirurgiao_patela','peixe_borboleta'],
        'abissal':['peixe_pescador_abissal','peixe_vibora','enguia_pelicano']}
    for name,selected in scenes.items():
        state=state_for(selected);view=AquariumView(lambda:state,ESPECIES)
        for detail in (1,2):
            kwargs={'detail':detail} if improved else {}
            tank=view.render_image(phase=0,**kwargs)
            if not improved and detail==2:tank=tank.scaled(512,256,Qt.IgnoreAspectRatio,Qt.FastTransformation)
            save(tank,f'tanque-{name}-{detail}x.png')
        if name=='iniciais':
            host=SyntheticHost(state);dialog=MuseuDialog(host)
            dialog.setAttribute(Qt.WA_DontShowOnScreen,True)
            dialog.show();app.processEvents();dialog.aquario.timer.stop();dialog.aquario.phase=0
            for width,height,kind in ((640,700,'desktop'),(320,568,'compacto')):
                dialog.resize(width,height);app.processEvents();dialog.aquario.timer.stop()
                dialog.aquario.phase=0;app.processEvents()
                save(dialog.grab().toImage(),f'museu-{kind}.png')
            dialog.close();host.close()
        view.close()
    # Read-only rendering must not mutate the shared non-museum sprite cache.
    cache_preserved=all(old_hashes[id_]==hashlib.sha256(bytes(species_image(id_).constBits())).hexdigest() for id_ in ids)
    if not cache_preserved:raise ValueError('Shared fishing sprite cache was modified.')
    hashes={id_:hashlib.sha256(bytes(image(id_).constBits())).hexdigest() for id_ in ids}
    files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted([*root.glob('*.py'),*(root/'assets').rglob('*.json')])}
    report=dict(label=args.label,improved=improved,python=platform.python_version(),
        pyside=qt_binding,platform=platform.system(),eligible_fish=len(ids),
        unique_sprites=len(set(hashes.values())),sprite_hashes=hashes,
        unchanged_shared_cache=cache_preserved,save_created=(profile/'save.json').exists(),
        product_and_json_sha256=files,
        scope='Actual museum widgets, frozen phase 0, synthetic in-memory discovery/size records. No game engine, persistence, Android or integration suite.',
        outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.png'))})
    (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('label','eligible_fish','unique_sprites','unchanged_shared_cache','save_created')}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
