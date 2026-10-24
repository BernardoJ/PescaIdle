"""Focused real-Qt demo checks. Synthetic profiles, no physical input/Android."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    QA = args.out.resolve()
else:
    QA = ROOT / 'qa' / ('demo-tests-' + uuid.uuid4().hex)
if not QA.is_relative_to(ROOT / 'qa'):
    raise ValueError('Saída dos testes deve ficar em qa deste candidato.')
QA.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT))
os.environ.update(PESCA_IDLE_DEMO_DIR=str(QA / 'guard'),
                  QT_QPA_PLATFORM=os.getenv('PESCA_IDLE_QT_TEST_PLATFORM', 'windows' if os.name=='nt' else 'offscreen'))
from tools.demo_tamanhos import prepare_environment, initialize_profile, read_fixture, identification
prepare_environment()  # MUST precede every product import.
from PySide6.QtCore import Qt, QRectF, QEvent
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from pesca_ui import configure_app
import pesca_idle as game_module
from pesca_save import SaveError, SaveStore
from pesca_museu_ui import MuseuDialog
from pesca_museu import change_exhibit
from pesca_tamanho_visual import scale_for, draw_fish
from pesca_tamanhos import exhibit
from pesca_especies_visual import species_image
from tools.demo_tamanhos_ui import DemoGame, DemoPanel, demo_now

APP = QApplication.instance() or QApplication([])
APP.setQuitOnLastWindowClosed(False)
configure_app(APP)
INFO = identification()
OBSERVED = {}


def drain():
    APP.processEvents()
    APP.sendPostedEvents(None, QEvent.DeferredDelete)


def evidence(widget, filename, scenario):
    shot = widget.grab().toImage()
    image = QImage(shot.width(), shot.height()+40, QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor('#142334'))
    painter = QPainter(image)
    painter.setFont(QFont('Segoe UI', 9))
    painter.setPen(QColor('#ffe3ac'))
    painter.drawText(QRectF(8,0,image.width()-16,40), Qt.AlignVCenter|Qt.TextWordWrap,
                     INFO['source_commit'][:12]+' · '+INFO['source_snapshot'][:8]+' · '+scenario)
    painter.drawImage(0,40,shot)
    painter.end()
    image.save(str(QA / filename))


class DemoTests(unittest.TestCase):
    def session(self, name, mobile=False):
        os.environ['PESCA_IDLE_MOBILE'] = '1' if mobile else '0'
        configure_app(APP)
        os.environ['PESCA_IDLE_DEMO_DIR'] = str(QA / name)
        path = prepare_environment()
        initialize_profile(path, demo_now())
        game_module.SAVE_PATH = path
        game = DemoGame()
        game.setAttribute(Qt.WA_DontShowOnScreen, True)
        game.show()
        panel = DemoPanel(game, path)
        game.demo_panel = panel
        panel.setAttribute(Qt.WA_DontShowOnScreen, True)
        panel.show()
        self.addCleanup(lambda:game.close() if not game._closed else None)
        drain()
        return game, panel, path

    def full_session(self, name, mobile=False):
        game, panel, path = self.session(name, mobile)
        for index, step in enumerate(read_fixture()['steps']):
            QTest.mouseClick(panel.capture, Qt.LeftButton)
            drain()
            self.assertEqual(game.estado['demo_tamanhos']['next_step'], index+1, panel.last.text())
            self.assertEqual(game._last_result['size_news'], step['expected_news'])
        self.assertFalse(panel.capture.isEnabled())
        return game, panel, path

    def test_01_environment_guard_and_ordinary_sentinel(self):
        sentinel = QA / 'synthetic-personal' / 'PescaIdle' / 'save.json'
        sentinel.parent.mkdir(parents=True)
        sentinel.write_bytes(b'synthetic-personal-sentinel-do-not-open')
        os.environ.update(PESCA_IDLE_SAVE_PATH=str(sentinel), APPDATA=str(sentinel.parent.parent))
        game, panel, path = self.session('isolated')
        self.assertNotEqual(path, sentinel)
        self.assertEqual(game.estado['inventario_por_id'], {})
        game.timer_save.timeout.emit()  # Actual autosave callback.
        self.assertTrue(game.close())
        drain()
        self.assertEqual(sentinel.read_bytes(), b'synthetic-personal-sentinel-do-not-open')
        self.assertEqual(sorted(p.name for p in sentinel.parent.iterdir()), ['save.json'])
        for forbidden in (ROOT / 'perfil-piloto', ROOT / 'unrelated-demo-folder'):
            os.environ['PESCA_IDLE_DEMO_DIR'] = str(forbidden)
            with self.assertRaises(ValueError):prepare_environment()
        OBSERVED['isolation'] = {'synthetic_personal_sentinel_unchanged':True, 'autosave_close':True}

    def test_02_capture_record_flow_and_evidence(self):
        game, panel, path = self.session('capture-flow')
        evidence(panel, 'roteiro.png', 'Painel isolado · início')
        captures = []
        expected = ('Primeiro registro', 'Novo menor pessoal', 'Novo maior pessoal', 'Sem novo recorde')
        for index, step in enumerate(read_fixture()['steps']):
            QTest.mouseClick(panel.capture, Qt.LeftButton)
            drain()
            self.assertEqual(game.estado['demo_tamanhos']['next_step'], index+1, panel.last.text())
            self.assertEqual(game._last_result['measurement']['mm'], step['mm'])
            self.assertEqual(game._last_result['size_news'], step['expected_news'])
            if index < 4:
                self.assertIn(expected[index], panel.last.text())
                game.repaint()
                QTest.qWait(30)
                captures.append(game.grab().toImage())
        width, height = captures[0].width(), captures[0].height()
        sheet = QImage(width*2, (height+44)*2, QImage.Format_ARGB32_Premultiplied)
        sheet.fill(QColor('#142334'))
        painter = QPainter(sheet)
        painter.setPen(QColor('#ffe3ac'))
        painter.setFont(QFont('Segoe UI', 10))
        for i, shot in enumerate(captures):
            x, y = (i%2)*width, (i//2)*(height+44)
            painter.drawText(QRectF(x+8,y,width-16,44), Qt.AlignVCenter|Qt.TextWordWrap,
                             INFO['source_commit'][:12]+' · '+expected[i])
            painter.drawImage(x,y+44,shot)
        painter.end()
        sheet.save(str(QA / 'capturas-primeiro-menor-maior-sem-recorde.png'))
        self.assertEqual(game.estado['inventario_por_id'], {'lambari':4,'tilapia_do_nilo':3,'carpa_comum':3})
        self.assertEqual(game.estado['medidas_peixes']['quantity'],10)
        self.assertEqual(game.estado['museu']['aquario'], ['lambari','tilapia_do_nilo','carpa_comum'])
        before = copy.deepcopy(game.estado)
        self.assertIsNone(game.next_capture())
        self.assertEqual(before, game.estado)
        OBSERVED['fixture'] = {'captures':10, 'measured':10, 'record_sequence':expected, 'source_seed':read_fixture()['seed']}

    def test_03_exhibit_choices_autosave_close_reopen(self):
        game, panel, path = self.full_session('reopen')
        QTest.mouseClick(panel.museum_button,Qt.LeftButton)
        drain()
        museum = panel.museum
        museum.setAttribute(Qt.WA_DontShowOnScreen,True)
        museum.resize(640,700)
        drain()
        evidence(museum, 'museu-maiores.png', 'Três espécies · maiores ativos')
        money = game.estado['moedas_centavos']
        inventory = copy.deepcopy(game.estado['inventario_por_id'])
        for slot, key in ((0, Qt.Key_End), (1, Qt.Key_Home), (2, Qt.Key_End)):
            museum.scroll.ensureWidgetVisible(museum.specimen_selectors[slot])
            museum.specimen_selectors[slot].setFocus()
            QTest.keyClick(museum.specimen_selectors[slot],key)
            drain()
        self.assertEqual(game.estado['museu']['exemplares'],['menor','maior','menor'])
        self.assertIn('4 cm',museum.specimen_selectors[0].currentText())
        self.assertIn('Em exposição: menor exemplar',museum.details[0].text())
        museum.scroll.verticalScrollBar().setValue(0)
        drain()
        evidence(museum, 'museu-menor-selecionado.png', 'Menor Lambari ativo · 4 cm')
        game.timer_save.timeout.emit()
        records = copy.deepcopy(game.estado['medidas_peixes'])
        choices = copy.deepcopy(game.estado['museu'])
        museum.accept()
        drain()
        self.assertTrue(game.close())
        drain()
        reopened = DemoGame()
        reopened.setAttribute(Qt.WA_DontShowOnScreen, True)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.estado['medidas_peixes'],records)
        self.assertEqual(reopened.estado['museu'],choices)
        self.assertEqual(reopened.estado['moedas_centavos'],money)
        self.assertEqual(reopened.estado['inventario_por_id'],inventory)
        self.assertEqual(reopened.estado['demo_tamanhos']['next_step'],10)
        self.assertTrue(reopened.pausado)
        OBSERVED['reopen'] = {'choices_preserved':True,'records_preserved':True,'no_extra_reward':True}

    def test_04_interrupted_pending_resumes_without_reroll(self):
        game, panel, path = self.session('interrupted')
        class Interrupted(RuntimeError):pass
        commit = game._commit
        def stop_after_pending(state, *args, **kwargs):
            ok = commit(state,*args,**kwargs)
            if ok and state['pesca_pendente'] is not None:raise Interrupted()
            return ok
        with patch.object(game,'_commit',side_effect=stop_after_pending), self.assertRaises(Interrupted):
            game.next_capture()
        pending = copy.deepcopy(game.estado['pesca_pendente'])
        self.assertTrue(game.close())
        drain()
        again = DemoGame()
        again.setAttribute(Qt.WA_DontShowOnScreen,True)
        self.addCleanup(again.close)
        result = again.next_capture()
        self.assertEqual(result['id'],pending['id'])
        self.assertEqual(result['measurement'],pending['measurement'])
        self.assertEqual(again.estado['medidas_peixes']['quantity'],1)
        self.assertEqual(again.estado['demo_tamanhos']['next_step'],1)

    def test_05_save_failure_restores_choice_and_shows_error(self):
        game, panel, path = self.full_session('failure',mobile=True)
        museum = MuseuDialog(game)
        museum.setAttribute(Qt.WA_DontShowOnScreen,True)
        museum.resize(320,568)
        museum.show()
        drain()
        old = path.read_bytes()
        real_replace = os.replace
        def fail_target(src,dst):
            if Path(dst)==path:raise OSError('falha sintética de gravação')
            return real_replace(src,dst)
        with patch('pesca_save.os.replace',side_effect=fail_target):
            museum.specimen_selectors[0].setCurrentIndex(1)
        for _ in range(4):drain()
        self.assertEqual(path.read_bytes(),old)
        self.assertEqual(museum.specimen_selectors[0].currentData(),'maior')
        self.assertIn('Seleção anterior mantida',museum.feedback.text())
        y=museum.feedback.mapTo(museum.scroll.viewport(),museum.feedback.rect().center()).y()
        self.assertTrue(0<=y<museum.scroll.viewport().height())
        evidence(museum,'erro-selecao-320.png','320×568 · falha sintética · seleção preservada')
        museum.accept()
        drain()
        self.assertTrue(game.salvar())  # Fault removed; normal shutdown can now persist.

    def test_06_empty_legacy_and_supported_viewports(self):
        game,panel,path=self.session('empty',mobile=True)
        museum=MuseuDialog(game)
        museum.setAttribute(Qt.WA_DontShowOnScreen,True)
        museum.resize(320,568);museum.show();drain()
        self.assertIn('Aquário vazio',museum.status.text())
        self.assertFalse(museum.specimen_selectors[0].isEnabled())
        evidence(museum,'museu-vazio-320.png','320×568 · vazio · escolhas desabilitadas')
        legacy=copy.deepcopy(game.estado)
        legacy['inventario_por_id']['pacu']=1
        legacy['legado_sem_contexto']['pacu']=1
        legacy['total_pescados']=1
        self.assertTrue(game._commit(change_exhibit(legacy,0,'pacu')))
        museum.refresh();drain()
        self.assertIn('Sem exemplar medido',museum.details[0].text())
        self.assertFalse(museum.specimen_selectors[0].isEnabled())
        museum.accept();drain()
        game,panel,path=self.full_session('viewport',mobile=True)
        museum=MuseuDialog(game)
        museum.setAttribute(Qt.WA_DontShowOnScreen,True)
        museum.show()
        for width,height in ((320,568),(360,800),(512,288)):
            museum.resize(width,height);drain()
            self.assertEqual(museum.width(),width)
            for combo in museum.specimen_selectors:
                museum.scroll.ensureWidgetVisible(combo);drain()
                self.assertLessEqual(combo.geometry().right(),museum.scroll.widget().width())
                self.assertGreater(combo.width(),200)
            museum.scroll.verticalScrollBar().setValue(museum.scroll.verticalScrollBar().maximum());drain()
            if width==320:evidence(museum,'museu-escolhas-320.png','320×568 · comprimentos nas escolhas')
            self.assertTrue(museum.back.isEnabled())
        museum.accept();drain()
        OBSERVED['qt_viewports']=[[320,568],[360,800],[512,288],[640,700]]

    def test_07_three_fish_bounds_separation_and_art_unchanged(self):
        game,panel,path=self.full_session('bounds')
        museum=MuseuDialog(game)
        museum.setAttribute(Qt.WA_DontShowOnScreen,True)
        original={sid:hashlib.sha256(bytes(species_image(sid).constBits())).hexdigest()
                  for sid in game.estado['museu']['aquario']}
        checks=0
        for choices in (['maior']*3,['menor','maior','menor']):
            state=copy.deepcopy(game.estado);state['museu']['exemplares']=choices
            self.assertTrue(game._commit(state))
            for phase in (0,5,10,17,25,35,48,60,75,90,110,130):
                rectangles=[]
                for sid,x,y,reverse in museum.aquario.fish_positions(phase):
                    slot=game.estado['museu']['aquario'].index(sid)
                    scale=scale_for(exhibit(game.estado,slot),sid)
                    box=QRectF(x-18*scale,y-12*scale,36*scale,24*scale)
                    self.assertGreaterEqual(box.left(),16);self.assertLessEqual(box.right(),240)
                    self.assertGreaterEqual(box.top(),16);self.assertLessEqual(box.bottom(),106)
                    self.assertTrue(all(not box.intersects(other) for other in rectangles))
                    rectangles.append(box);checks+=1
                self.assertFalse(museum.aquario.render_image(phase).isNull())
        for sid,digest in original.items():
            self.assertEqual(hashlib.sha256(bytes(species_image(sid).constBits())).hexdigest(),digest)
        museum.accept();drain()
        OBSERVED['tank']={'bounds_and_separation_checks':checks,'uniform_scale_unchanged':True,'shared_art_unchanged':True}

    def test_08_invalid_demo_file_and_normal_entry(self):
        os.environ['PESCA_IDLE_DEMO_DIR']=str(QA/'invalid-marker')
        path=prepare_environment();path.write_bytes(b'{"synthetic-file":"not-a-demo"}')
        old=path.read_bytes()
        with self.assertRaises(ValueError):prepare_environment()
        self.assertEqual(path.read_bytes(),old)
        command=[sys.executable,'-B','-c',
                 "import runpy,sys;runpy.run_path('piloto_entry.py',run_name='entry_import_test');print('tools.demo_tamanhos' in sys.modules)"]
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'False')

    def test_09_capture_contrast_preserves_uniform_body_size(self):
        from pesca_tamanhos import sample, rule_snapshot
        original=hashlib.sha256(bytes(species_image('lambari').constBits())).hexdigest()
        counts=[]
        for quantile in (0,.5,1):
            results=[]
            for contrast in (False,True):
                image=QImage(80,60,QImage.Format_ARGB32_Premultiplied)
                image.fill(Qt.transparent)
                painter=QPainter(image)
                bounds=draw_fish(painter,'lambari',40,30,sample(quantile,rule_snapshot('lambari')),
                                 base_scale=2/3,contrast=contrast)
                painter.end()
                opaque=sum(image.pixelColor(x,y).alpha()>0 for x in range(80) for y in range(60))
                results.append((bounds,opaque))
            self.assertEqual(results[0][0],results[1][0])
            self.assertGreater(results[1][1],results[0][1])
            counts.append(results[1][1])
        self.assertEqual(counts,sorted(counts))
        self.assertEqual(hashlib.sha256(bytes(species_image('lambari').constBits())).hexdigest(),original)

    def test_10_resolved_file_redirect_is_rejected_before_read(self):
        folder=QA/'resolved-file-guard'
        redirected=ROOT/'perfil-piloto'/'save.json'
        # Model a resolved link without creating OS links or changing privileges.
        with patch('tools.demo_tamanhos.validate_profile_path',side_effect=[folder,redirected]), \
                patch.object(Path,'read_text',side_effect=AssertionError('No file may be read')):
            with self.assertRaisesRegex(ValueError,'redirecionar'):
                prepare_environment()


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DemoTests))
    summary={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'identification':INFO,'qt_platform':APP.platformName(),
             'input':'QTest injected, hidden Qt widgets; not physical input/Android',
             'observed':OBSERVED}
    (QA/'resultado.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    sys.exit(0 if result.wasSuccessful() else 1)
