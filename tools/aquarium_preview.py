"""Disposable visual demonstration. No game engine, SaveStore or real profiles."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import uuid

ROOT = Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]


def isolate(output=None, root=ROOT):
    """Call BEFORE Qt/product imports. Never reuse a preexisting directory."""
    root = Path(root).resolve()
    output = Path(output).resolve() if output else root/'qa'/('aquario-demo-'+uuid.uuid4().hex)
    if not output.is_relative_to(root/'qa') or output == root/'qa' or output.exists():
        raise ValueError('Use uma pasta NOVA dentro de qa/ nesta cópia.')
    output.mkdir(parents=True)
    for name in ('appdata','localappdata','tmp'):
        (output/name).mkdir()
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(output/'synthetic-never-written.json'),
        APPDATA=str(output/'appdata'),LOCALAPPDATA=str(output/'localappdata'),
        TEMP=str(output/'tmp'),TMP=str(output/'tmp'))
    sys.path.insert(0,str(root))
    return output


def synthetic_state(selected=None, choices=None):
    from pesca_catalogo import ESPECIES
    from pesca_tamanhos import RULES, rule_snapshot, band
    records={}
    for id_ in RULES:
        rule=rule_snapshot(id_)
        def specimen(kind):
            mm=rule['min_mm' if kind=='menor' else 'max_mm']
            return dict(mm=mm,band=band(mm,rule),rule=copy.deepcopy(rule),
                event_id='synthetic-visual:'+id_+':'+kind,utc=1792411200,
                map_id='enseada_do_poente',periodo_id='meio_dia')
        records[id_]=dict(n=2,menor=specimen('menor'),maior=specimen('maior'))
    return dict(inventario_por_id={id_:2 for id_,s in ESPECIES.items() if s['categoria']=='peixe'},
        museu=dict(version=1,aquario=selected or ['lambari','tilapia_do_nilo','carpa_comum'],
                   exemplares=choices or ['maior']*3),
        medidas_peixes=dict(version=1,records=records))


def make_demo(app):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
    from pesca_museu_ui import MuseuDialog
    class MemoryHost(QWidget):
        def __init__(self):
            super().__init__();self.estado=synthetic_state();self._save_error=''
        def _commit(self,state):
            self.estado=copy.deepcopy(state)  # Demonstration choices, MEMORY ONLY.
            return True
    host=MemoryHost();dialog=MuseuDialog(host)
    dialog.setWindowTitle('PescaIdle - Demonstração visual do aquário (sem save)')
    badge=QLabel('DEMONSTRAÇÃO VISUAL · DADOS SINTÉTICOS · SEM SAVE')
    badge.setWordWrap(True);badge.setStyleSheet('color: #ffe3ac; font-weight: bold;')
    dialog.body.insertWidget(0,badge)
    controls=QWidget();controls_layout=QVBoxLayout(controls)
    controls_layout.setContentsMargins(0,0,0,0)
    row=QHBoxLayout();controls_layout.addLayout(row)
    pause=QPushButton('Pausar');step=QPushButton('Próximo quadro');step.setEnabled(False)
    preset=QComboBox();preset.setAccessibleName('Grupo de exemplos visuais')
    groups={
        'Piloto':['lambari','tilapia_do_nilo','carpa_comum'],
        'Rio':['traira','pintado','pirarara'],
        'Recife':['peixe_palhaco','cirurgiao_patela','peixe_borboleta'],
        'Formas especiais':['cavalinho_do_mar_pigmeu','peixe_lua','celacanto_comorense'],
        'Abissais':['peixe_pescador_abissal','peixe_vibora','enguia_pelicano']}
    for name in groups:preset.addItem(name)
    row.addWidget(pause);row.addWidget(step);controls_layout.addWidget(preset)
    dialog.body.insertWidget(1,controls)
    def toggle():
        paused=pause.text()=='Pausar'
        dialog.aquario.timer.blockSignals(paused)
        dialog.aquario.clock.start()
        pause.setText('Continuar' if paused else 'Pausar');step.setEnabled(paused)
    def next_frame():
        dialog.aquario.phase+=.2;dialog.aquario.update()
    def choose_group(name):
        host.estado['museu']['aquario']=groups[name][:]
        dialog._signature=None;dialog.refresh()
    pause.clicked.connect(toggle);step.clicked.connect(next_frame)
    preset.currentTextChanged.connect(choose_group)
    dialog.demo_controls=dict(pause=pause,step=step,preset=preset)
    dialog.demo_host=host  # Keep synthetic parent alive.
    return dialog


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args()
    if args.smoke and args.out is None:parser.error('--smoke exige --out explícito.')
    try:
        output=isolate(args.out)
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        from pesca_ui import configure_app
        app=QApplication([]);app.setQuitOnLastWindowClosed(False);configure_app(app)
        dialog=make_demo(app)
        if args.smoke:dialog.setAttribute(Qt.WA_DontShowOnScreen,True)
        dialog.show();app.processEvents()
        if args.smoke:
            from PySide6.QtTest import QTest
            QTest.mouseClick(dialog.demo_controls['pause'],Qt.LeftButton)
            assert dialog.aquario.timer.signalsBlocked()
            old_phase=dialog.aquario.phase
            QTest.mouseClick(dialog.demo_controls['step'],Qt.LeftButton)
            assert dialog.aquario.phase>old_phase
            dialog.demo_controls['preset'].setCurrentIndex(3)
            assert dialog.demo_host.estado['museu']['aquario'][0]=='cavalinho_do_mar_pigmeu'
            for width,height in ((640,700),(320,568)):
                dialog.resize(width,height);app.processEvents()
                assert (dialog.width(),dialog.height())==(width,height)
                assert dialog.grab().save(str(output/('demo-'+str(width)+'.png')))
            dialog.demo_controls['preset'].setCurrentIndex(0)
            dialog.specimen_selectors[0].setCurrentIndex(1)
            assert dialog.demo_host.estado['museu']['exemplares'][0]=='menor'
            QTest.mouseClick(dialog.demo_controls['pause'],Qt.LeftButton)
            assert not dialog.aquario.timer.signalsBlocked()
            QTest.qWait(250)
            assert dialog.aquario.phase>old_phase+.2
            dialog.close();app.processEvents()
            assert not dialog.aquario.timer.isActive()
            assert not (output/'synthetic-never-written.json').exists()
            (output/'smoke.json').write_text(json.dumps(dict(pause=True,step=True,
                presets=True,viewports=[640,320],specimen_choice=True,
                timer_advanced=True,timer_stopped_on_close=True,
                save_created=False,frozen=bool(getattr(sys,'frozen',False))),indent=2),encoding='utf-8')
            return 0
        dialog.finished.connect(app.quit)
        return app.exec()
    except (OSError,ValueError,AssertionError) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(run())
