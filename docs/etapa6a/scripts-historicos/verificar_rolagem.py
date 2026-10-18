"""Check the existing museum footer and exit; no production edits."""
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'qa/rolagem'
OUT.mkdir(exist_ok=False)
PROFILE = tempfile.TemporaryDirectory(prefix='rodape-', dir=ROOT / 'qa/temporarios')
os.environ.update(PESCA_IDLE_SAVE_PATH=str(Path(PROFILE.name) / 'guard.json'),
                  APPDATA=str(Path(PROFILE.name) / 'appdata'),
                  LOCALAPPDATA=str(Path(PROFILE.name) / 'localappdata'),
                  QT_QPA_PLATFORM='windows', QT_SCALE_FACTOR='1.25')
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'snapshot-verificado'))
from PySide6.QtCore import QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel
from pesca_ui import configure_app
from pesca_museu_ui import MuseuDialog
import pesca_idle as game

app = QApplication([])
configure_app(app)
g = game.JogoPesca(wall_clock=lambda: 1792072800, monotonic_clock=lambda: 0)
g.relogio.stop(); g.timer_save.stop()
g.pausado = True; g.estado['pausado'] = True
g.estado['inventario_por_id'] = {'lambari': 1, 'peixe_palhaco': 2, 'cirurgiao_patela': 3}
g.estado['total_pescados'] = 6
g.estado['museu'] = {'version': 1, 'aquario': ['lambari', 'peixe_palhaco', 'cirurgiao_patela']}
if not g.salvar():
    raise RuntimeError('Synthetic save failed')
records = []
for name, width, height, mobile in [('windows125', 640, 700, False),
                                    ('mobile320', 320, 568, True),
                                    ('mobile360', 360, 800, True)]:
    os.environ['PESCA_IDLE_MOBILE'] = '1' if mobile else '0'
    configure_app(app)
    d = MuseuDialog(g)
    d.resize(width, height); d.show(); QTest.qWait(60)
    footer = next(label for label in d.findChildren(QLabel)
                  if label.text().startswith('Ilustrações da coleção'))
    d.scroll.ensureWidgetVisible(d.back)
    QTest.qWait(60)
    footer_visible = footer.visibleRegion().contains(footer.rect())
    back_visible = d.back.visibleRegion().contains(d.back.rect())
    if not footer_visible or not back_visible:
        raise RuntimeError('Footer/back inaccessible: ' + name)
    d.grab().save(str(OUT / (name + '-rodape.png')))
    QTest.keyClick(d, Qt.Key_Escape); app.processEvents()
    if d.aquario.timer.isActive():
        raise RuntimeError('Aquarium timer retained on Escape')
    records.append(dict(name=name, viewport=[d.width(), d.height()],
                        device_ratio=d.devicePixelRatioF(), footer_fully_visible=True,
                        exit_fully_visible=True, escape_stops_timer=True))
    d.deleteLater(); app.sendPostedEvents(None, QEvent.DeferredDelete)
g.close()
if g._store.lock is not None:
    raise RuntimeError('Synthetic lock not released')
(OUT / 'rolagem.json').write_text(json.dumps(dict(records=records, profile_isolated=True,
    platform='Windows native; desktop mobile preview, not a physical phone'), indent=2), encoding='utf-8')
print(json.dumps(records))
PROFILE.cleanup()
