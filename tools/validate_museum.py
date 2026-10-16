"""Museum contracts, synthetic profiles and Qt evidence; no personal save."""
import copy
import gc
import json
import os
from pathlib import Path
import random
import statistics
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
PROFILE = tempfile.TemporaryDirectory(prefix='pesca-museum-qa-')
os.environ.update(PESCA_IDLE_SAVE_PATH=str(Path(PROFILE.name)/'guard.json'),
                  APPDATA=str(Path(PROFILE.name)/'appdata'),
                  LOCALAPPDATA=str(Path(PROFILE.name)/'localappdata'))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QPushButton
from shiboken6 import isValid
from pesca_museu import (empty_museum, validate_museum, eligible_species,
                         slot_status, change_exhibit)
from pesca_museu_ui import MuseuDialog
from pesca_catalogo import ESPECIES
from pesca_save import SaveStore, SaveError, migrate
from pesca_pescaria import FishingEngine
from pesca_offline import replay, schedule
from pesca_moedas import set_balance
from pesca_conquistas import grant
from pesca_loja import CATALOGO
from pesca_ui import configure_app
from pesca_android import MobileLifecycle
import pesca_idle as game

APP = QApplication.instance() or QApplication([])
configure_app(APP)
NOW = 1792072800
IDS = ('lambari','peixe_palhaco','cirurgiao_patela','tilapia_do_nilo')
OUT = Path(os.environ.get('PESCA_IDLE_QA_DIR',PROFILE.name))
OUT.mkdir(parents=True,exist_ok=True)


def drain():
    APP.processEvents()
    APP.sendPostedEvents(None,QEvent.DeferredDelete)


class MuseumTests(unittest.TestCase):
    def fresh(self):
        state = migrate({},game.ESTADO_PADRAO,NOW)
        state['perfil_id'] = 'synthetic-museum'
        state['rng_state'] = random.Random(41).getstate()
        return state

    def known(self):
        s = self.fresh()
        s['inventario_por_id'] = {id_:i+1 for i,id_ in enumerate(IDS)}
        s['total_pescados'] = sum(s['inventario_por_id'].values())
        return s

    def store(self,name):
        store = SaveStore(Path(PROFILE.name)/(name+'.json'))
        self.addCleanup(store.close)
        return store

    def gui(self):
        game.SAVE_PATH = Path(PROFILE.name)/(self._testMethodName+'-'+str(time.monotonic_ns())+'.json')
        g = game.JogoPesca(wall_clock=lambda:NOW,monotonic_clock=lambda:0)
        g.pausado = True
        g.estado['pausado'] = True
        g.estado['inventario_por_id'] = {id_:i+1 for i,id_ in enumerate(IDS)}
        g.estado['total_pescados'] = sum(g.estado['inventario_por_id'].values())
        self.assertTrue(g.salvar())
        self.addCleanup(g.close)
        return g

    def test_01_eligibility_and_independent_selections(self):
        s = self.fresh()
        self.assertEqual(eligible_species(s),())
        s['inventario_por_id'] = {id_:1 for id_ in ESPECIES}
        allowed = eligible_species(s)
        self.assertEqual(len(allowed),68)
        self.assertEqual(len(set(ESPECIES)-set(allowed)),20)
        self.assertEqual(eligible_species(s,{}),())
        original = copy.deepcopy(s)
        for slot,id_ in enumerate(IDS[:3]):
            s = change_exhibit(s,slot,id_)
        self.assertEqual(s['museu']['aquario'],list(IDS[:3]))
        self.assertEqual({k:v for k,v in s.items() if k!='museu'},
                         {k:v for k,v in original.items() if k!='museu'})
        self.assertEqual(original['museu'],empty_museum())
        self.assertEqual(change_exhibit(s,0,IDS[0]),s)
        s = change_exhibit(s,0,IDS[3])
        s = change_exhibit(s,1,None)
        self.assertEqual(change_exhibit(s,1,None),s)
        self.assertEqual(s['museu']['aquario'],[IDS[3],None,IDS[2]])

    def test_02_reject_invalid_actions_without_mutation(self):
        s = self.known()
        s = change_exhibit(s,0,IDS[0])
        s['inventario_por_id']['vaquita'] = 1
        before = copy.deepcopy(s)
        for slot,id_ in ((1,IDS[0]),(1,'vaquita'),(1,'unknown-id'),(1,'tubarao_branco'),
                         (3,IDS[1]),(-1,None),(True,IDS[1]),(0,['bad'])):
            with self.subTest(slot=slot,id=id_),self.assertRaises(ValueError):
                change_exhibit(s,slot,id_)
            self.assertEqual(s,before)
        for id_,species in ESPECIES.items():
            if species['categoria']=='especial':
                s['inventario_por_id'][id_]=1
                with self.subTest(special=id_),self.assertRaises(ValueError):
                    change_exhibit(s,1,id_)

    def test_03_legacy_migrations_backups_and_idempotence(self):
        for version in (1,2,3):
            s = self.known()
            set_balance(s,123.45)
            s.update(vara=3,barco=3,pecas_vara=2,conquistas=['vestir_todos'],custom_future={'keep':[7]})
            raw = copy.deepcopy(s)
            raw.pop('museu')
            raw['schema_version'] = version
            if version<3:
                raw.pop('moedas_centavos')
            if version==1:
                raw['inventario'] = {ESPECIES[id_]['nome']:n for id_,n in s['inventario_por_id'].items()}
                raw.pop('inventario_por_id')
            blob = json.dumps(raw,ensure_ascii=False).encode('utf-8')
            store = self.store('legacy-'+str(version))
            store.path.write_bytes(blob)
            loaded = store.load(game.ESTADO_PADRAO,NOW)
            self.assertEqual(loaded['museu'],empty_museum())
            for key in ('moedas_centavos','vara','barco','pecas_vara','cosmeticos','equipados','conquistas','custom_future'):
                self.assertEqual(loaded[key],s[key])
            self.assertEqual(loaded['inventario_por_id'],s['inventario_por_id'])
            self.assertEqual(loaded['registros_regionais'],s['registros_regionais'])
            self.assertEqual(migrate(loaded,game.ESTADO_PADRAO,NOW),loaded)
            if version<3:
                backup = store.path.with_name('legacy-'+str(version)+('.pre-expansao-v1.json' if version==1 else '.pre-schema-2.json'))
                self.assertEqual(backup.read_bytes(),blob)
            else:
                self.assertEqual(store.path.read_bytes(),blob)
            store.save(loaded)
            if version==3:
                self.assertEqual(store.backup_path.read_bytes(),blob)
            self.assertEqual(store.load(game.ESTADO_PADRAO,NOW)['museu'],empty_museum())

    def test_04_unknown_references_preserved_and_not_drawn(self):
        g = self.gui()
        state = copy.deepcopy(g.estado)
        state['museu'] = {'version':1,'aquario':['future-fish','vaquita','tubarao_branco'],'future_note':'keep'}
        self.assertTrue(g._commit(state))
        d = MuseuDialog(g)
        self.assertEqual(d.aquario.fish_positions(8),[])
        self.assertEqual([slot_status(g.estado,i) for i in range(3)],
                         ['referencia_desconhecida','encontro_especial','nao_descoberta'])
        self.assertIn('Referência',d.selectors[0].currentText())
        self.assertEqual(migrate(g.estado,game.ESTADO_PADRAO,NOW)['museu'],state['museu'])
        d.apply(0,IDS[0])
        self.assertEqual(g.estado['museu']['future_note'],'keep')
        self.assertEqual(g.estado['museu']['aquario'][1:3],['vaquita','tubarao_branco'])
        d.accept();d.deleteLater();drain()

    def test_05_invalid_exhibit_structure_and_atomic_recovery(self):
        store = self.store('failure')
        state = self.known();store.save(state)
        before = store.path.read_bytes()
        for museum in (None,[],{'version':2,'aquario':[None]*3},
                       {'version':1,'aquario':[None]*4}, {'version':1,'aquario':['x','x',None]},
                       {'version':1,'aquario':[[],None,None]}, {'version':1,'aquario':[' ',None,None]}):
            bad = copy.deepcopy(state);bad['museu']=museum
            with self.subTest(museum=museum),self.assertRaises(SaveError):
                store.save(bad)
            self.assertEqual(store.path.read_bytes(),before)
            malformed=json.dumps(bad).encode('utf-8')
            store.path.write_bytes(malformed)
            with self.assertRaises(SaveError):store.load(game.ESTADO_PADRAO,NOW)
            self.assertEqual(store.path.read_bytes(),malformed)
            store.path.write_bytes(before)
        real_replace = os.replace
        def failed(src,dst):
            if Path(dst)==store.path:raise OSError('synthetic disk full')
            return real_replace(src,dst)
        desired = change_exhibit(state,0,IDS[0])
        with patch('pesca_save.os.replace',side_effect=failed),self.assertRaises(SaveError):
            store.save(desired)
        self.assertEqual(store.path.read_bytes(),before)
        self.assertEqual(store.last_good['museu'],empty_museum())
        store.save(desired);store.save(change_exhibit(desired,1,IDS[1]))
        rejected = b'{synthetic broken json'
        store.path.write_bytes(rejected)
        with self.assertRaises(SaveError):store.load(game.ESTADO_PADRAO,NOW)
        self.assertTrue(store.backup_available(game.ESTADO_PADRAO,NOW))
        recovered = store.recover(game.ESTADO_PADRAO,NOW)
        self.assertEqual(recovered['museu']['aquario'],[IDS[0],None,None])
        self.assertEqual(next(store.path.parent.glob('failure.rejeitado-*.json')).read_bytes(),rejected)

    def test_06_controls_persistence_and_save_error(self):
        g = self.gui();d = MuseuDialog(g);d.show();drain()
        original = copy.deepcopy(g.estado)
        for slot,id_ in enumerate(IDS[:3]):
            d.selectors[slot].setCurrentIndex(d.selectors[slot].findData(id_))
        self.assertEqual(g.estado['museu']['aquario'],list(IDS[:3]))
        self.assertEqual({k:v for k,v in g.estado.items() if k not in ('museu','ultimo_salvo')},
                         {k:v for k,v in original.items() if k not in ('museu','ultimo_salvo')})
        d.apply(1,IDS[0]);self.assertIn('outro espaço',d.feedback.text())
        d.apply(1,IDS[3])
        self.assertEqual(g.estado['museu']['aquario'],[IDS[0],IDS[3],IDS[2]])
        d.scroll.ensureWidgetVisible(d.remove_buttons[2]);drain()
        QTest.mouseClick(d.remove_buttons[2],Qt.LeftButton)
        self.assertIsNone(g.estado['museu']['aquario'][2])
        disk = g._store.path.read_bytes()
        d.resize(360,568);d.selectors[0].setFocus()
        d.scroll.verticalScrollBar().setValue(0);drain()
        real_replace = os.replace
        def failed(src,dst):
            if Path(dst)==g._store.path:raise OSError('synthetic permission denied')
            return real_replace(src,dst)
        with patch('pesca_save.os.replace',side_effect=failed):d.apply(2,IDS[2])
        drain()
        self.assertIn('não salva',d.feedback.text());self.assertTrue(g.pausado)
        self.assertTrue(d.feedback.visibleRegion().contains(d.feedback.rect().center()))
        self.assertEqual(g._store.path.read_bytes(),disk)
        self.assertIsNone(g.estado['museu']['aquario'][2])
        d.accept();d.deleteLater();drain()
        expected = copy.deepcopy(g.estado['museu']);path=g._store.path
        g.close();self.assertIsNone(g._store.lock)
        # A real new game constructor reopens the same synthetic profile.
        game.SAVE_PATH = path
        reopened = game.JogoPesca(wall_clock=lambda:NOW,monotonic_clock=lambda:0)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.estado['museu'],expected)

    def test_07_repeated_open_close_and_suspend(self):
        g = self.gui();g.show();drain()
        seen=[]
        def close_dialog():
            d=APP.activeModalWidget()
            self.assertIsInstance(d,MuseuDialog)
            seen.append(d.aquario.timer)
            d.accept()
        for _ in range(50):
            QTimer.singleShot(0,close_dialog)
            g.abrir_museu();drain()
            self.assertEqual(len(g.findChildren(MuseuDialog)),0)
        gc.collect()
        self.assertTrue(all(not isValid(t) for t in seen))
        d=MuseuDialog(g);d.show();drain()
        self.assertTrue(d.aquario.timer.isActive())
        d.aquario.application_state(Qt.ApplicationSuspended)
        self.assertFalse(d.aquario.timer.isActive())
        phase=d.aquario.phase;QTest.qWait(80);self.assertEqual(d.aquario.phase,phase)
        d.aquario.application_state(Qt.ApplicationActive)
        self.assertTrue(d.aquario.timer.isActive())
        d.accept();self.assertFalse(d.aquario.timer.isActive());d.deleteLater();drain()

    def test_08_no_economy_rng_or_offline_side_effects(self):
        initial=self.known()
        changed=change_exhibit(initial,0,IDS[0])
        for seconds in (0,120,14400,28800):
            a,ra=replay(initial,NOW+seconds);b,rb=replay(changed,NOW+seconds)
            self.assertEqual(ra,rb)
            self.assertEqual({k:v for k,v in a.items() if k!='museu'}, {k:v for k,v in b.items() if k!='museu'})
            before=copy.deepcopy(b);grant(b,CATALOGO)
            # Aquarium cannot grant an achievement or award by itself.
            other=copy.deepcopy(a);grant(other,CATALOGO)
            self.assertEqual(b['conquistas'],other['conquistas'])
            self.assertEqual(b['museu'],changed['museu'])
            again,report=replay(before,NOW+seconds)
            self.assertEqual(report['gain'],0)
        schedule(initial,'enseada_do_poente',NOW+60,3600,NOW)
        with_exhibit=change_exhibit(initial,0,IDS[0])
        a,ra=replay(initial,NOW+1800);b,rb=replay(with_exhibit,NOW+1800)
        self.assertEqual(ra,rb);self.assertEqual(a['expedicao'],b['expedicao'])
        for s in (initial,changed):s['pausado']=True
        self.assertEqual(replay(initial,NOW+14400)[1],replay(changed,NOW+14400)[1])

    def test_09_visual_states_resolution_and_animation(self):
        g=self.gui()
        original=copy.deepcopy(g.estado)
        initial=copy.deepcopy(g.estado);initial['inventario_por_id']={};initial['total_pescados']=0
        self.assertTrue(g._commit(initial))
        d=MuseuDialog(g);d.show();drain()
        self.assertIn('Aquário vazio',d.status.text())
        self.assertFalse(d.selectors[0].isEnabled())
        d.grab().save(str(OUT/'museu-inicio.png'));d.accept();d.deleteLater();drain()
        self.assertTrue(g._commit(original))
        for name,ids in (('vazio',()),('um',IDS[:1]),('tres',IDS[:3])):
            state=copy.deepcopy(g.estado);state['museu']=empty_museum()
            for slot,id_ in enumerate(ids):state=change_exhibit(state,slot,id_)
            self.assertTrue(g._commit(state))
            d=MuseuDialog(g);d.resize(640,700);d.show();drain()
            self.assertEqual(len(d.aquario.fish_positions(0)),len(ids))
            if ids:self.assertNotEqual(d.aquario.fish_positions(0),d.aquario.fish_positions(8))
            d.aquario.phase=8;d.grab().save(str(OUT/('museu-'+name+'.png')))
            d.aquario.render_image(8).scaled(768,384,Qt.IgnoreAspectRatio,Qt.FastTransformation).save(str(OUT/('aquario-'+name+'.png')))
            if name=='tres':
                from PIL import Image
                frames=[]
                for frame in range(45):
                    img=d.aquario.render_image(frame/15).scaled(768,384,Qt.IgnoreAspectRatio,Qt.FastTransformation)
                    img=img.convertToFormat(QImage.Format_RGBA8888)
                    frames.append(Image.frombytes('RGBA',(img.width(),img.height()),bytes(img.constBits())).convert('RGB'))
                frames[0].save(OUT/'aquario-animado.gif',save_all=True,append_images=frames[1:],duration=66,loop=0)
            state_before=copy.deepcopy(g.estado)
            for _ in range(60):d.aquario.render_image(12)
            self.assertEqual(g.estado,state_before)
            d.accept();d.deleteLater();drain()
        d=MuseuDialog(g,catalogue={});d.show();drain();self.assertFalse(d.selectors[0].isEnabled())
        self.assertIn('Descubra um peixe',d.status.text())
        d.grab().save(str(OUT/'museu-catalogo-vazio.png'));d.accept();d.deleteLater();drain()
        old=os.environ.get('PESCA_IDLE_MOBILE')
        try:
            os.environ['PESCA_IDLE_MOBILE']='1';configure_app(APP)
            for w,h in ((360,800),(800,360),(512,288),(320,568)):
                d=MuseuDialog(g);d.resize(w,h);d.show();QTest.qWait(30)
                self.assertEqual((d.width(),d.height()),(w,h))
                self.assertLessEqual(d.scroll.widget().width(),d.scroll.viewport().width())
                for combo in d.selectors:self.assertGreaterEqual(combo.height(),44)
                d.scroll.ensureWidgetVisible(d.back);drain()
                self.assertTrue(d.back.visibleRegion().contains(d.back.rect().center()))
                d.scroll.verticalScrollBar().setValue(0);drain()
                d.grab().save(str(OUT/f'museu-preview-{w}x{h}.png'))
                d.accept();d.deleteLater();drain()
        finally:
            if old is None:os.environ.pop('PESCA_IDLE_MOBILE',None)
            else:os.environ['PESCA_IDLE_MOBILE']=old
            configure_app(APP)

    def test_10_performance_bounded_and_mobile_resume(self):
        g=self.gui();d=MuseuDialog(g);d.show();drain()
        for slot,id_ in enumerate(IDS[:3]):d.apply(slot,id_)
        timings=[];main=[]
        for i in range(210):
            t=time.perf_counter();d.aquario.render_image(i/15);timings.append((time.perf_counter()-t)*1000)
            t=time.perf_counter();g._render.render(g);main.append((time.perf_counter()-t)*1000)
        def stats(values):return {'median_ms':statistics.median(values[10:]),'p95_ms':sorted(values[10:])[189]}
        (OUT/'performance.json').write_text(json.dumps({'aquarium_3':stats(timings),'main_scene':stats(main),
            'frames':200,'max_exhibits':3,'animation_interval_ms':66,
            'backend':APP.platformName(),'device_ratio':g.devicePixelRatioF(),
            'limit':'Desktop render microbenchmark, not physical Android performance.'},indent=2))
        clock={'wall':NOW,'mono':0};g._wall=lambda:clock['wall'];g._monotonic=lambda:clock['mono']
        lifecycle=MobileLifecycle(APP,g);g.pausado=False;g.estado['pausado']=False
        exhibition=copy.deepcopy(g.estado['museu'])
        lifecycle.changed(Qt.ApplicationSuspended);d.aquario.application_state(Qt.ApplicationSuspended)
        clock['wall']+=120;clock['mono']+=120
        lifecycle.changed(Qt.ApplicationActive);d.aquario.application_state(Qt.ApplicationActive)
        self.assertEqual(g._last_offline['paid_seconds'],120)
        self.assertEqual(g.estado['museu'],exhibition)
        once=copy.deepcopy(g.estado);lifecycle.changed(Qt.ApplicationActive);self.assertEqual(g.estado,once)
        d.accept();d.deleteLater();drain()

    def test_11_qt_touch_and_mobile_menu_route(self):
        g=self.gui();g.show();drain()
        previous=os.environ.get('PESCA_IDLE_MOBILE')
        try:
            os.environ['PESCA_IDLE_MOBILE']='1';configure_app(APP)
            d=MuseuDialog(g);d.resize(360,800);d.show();drain()
            d.apply(0,IDS[0])
            button=d.remove_buttons[0]
            d.scroll.ensureWidgetVisible(button);drain()
            device=QTest.createTouchDevice()
            point=button.rect().center()
            QTest.touchEvent(button,device).press(0,point,button).commit()
            QTest.touchEvent(button,device).release(0,point,button).commit()
            QTest.qWait(250)
            self.assertIsNone(g.estado['museu']['aquario'][0])
            d.accept();d.deleteLater();drain()
            routed=[]
            def close_museum():
                dlg=APP.activeModalWidget()
                if isinstance(dlg,MuseuDialog):
                    routed.append('museum');dlg.accept()
            def click_menu():
                dlg=APP.activeModalWidget()
                for btn in dlg.findChildren(QPushButton):
                    if btn.text()=='Museu':
                        routed.append('menu');btn.click();QTimer.singleShot(30,close_museum);return
                dlg.reject()
            QTimer.singleShot(0,click_menu);g.abrir_menu();QTest.qWait(80);drain()
            self.assertEqual(routed,['menu','museum'])
            self.assertEqual(g.findChildren(MuseuDialog),[])
        finally:
            if previous is None:os.environ.pop('PESCA_IDLE_MOBILE',None)
            else:os.environ['PESCA_IDLE_MOBILE']=previous
            configure_app(APP)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(MuseumTests)
    if '--native-visual' in sys.argv:
        suite=unittest.TestSuite(MuseumTests(name) for name in ('test_06_controls_persistence_and_save_error','test_09_visual_states_resolution_and_animation','test_11_qt_touch_and_mobile_menu_route'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/'museum.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'profile_isolated':True,'backend':APP.platformName(),
        'python':sys.version,'qt':__import__('PySide6').__version__,
        'android_device_test':False},indent=2),encoding='utf-8')
    sys.exit(not result.wasSuccessful())
