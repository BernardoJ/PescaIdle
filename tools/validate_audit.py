"""Regression tests for the attached audit, exclusively synthetic profiles."""
import copy,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROFILE=tempfile.TemporaryDirectory(prefix='pesca-audit-')
os.environ['PESCA_IDLE_SAVE_PATH']=str(Path(PROFILE.name)/'gui.json')
os.environ['APPDATA']=str(Path(PROFILE.name)/'appdata')
os.environ['LOCALAPPDATA']=str(Path(PROFILE.name)/'localappdata')
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pesca_save import SaveStore,SaveError,migrate,SCHEMA
from pesca_moedas import cents,set_balance,credit,debit,reward,can_buy
from pesca_loja import CATALOGO,sold_items
from pesca_conquistas import grant,fashionista_progress
from pesca_pescaria import FishingEngine
from pesca_offline import replay
from PySide6.QtCore import Qt,QEvent
from PySide6.QtWidgets import QApplication,QDialog,QMessageBox
import pesca_idle as game
APP=QApplication.instance() or QApplication([])


class Audit(unittest.TestCase):
    def fresh(self):return migrate({},game.ESTADO_PADRAO,1800000000)
    def store(self,name):
        store=SaveStore(Path(PROFILE.name)/(name+'.json'));self.addCleanup(store.close);return store

    def test_F1_atomic_failure_and_backup(self):
        store=self.store('atomic');state=store.load(game.ESTADO_PADRAO,1800000000);store.save(state)
        before=store.path.read_bytes();stamp=state['ultimo_salvo'];candidate=copy.deepcopy(state);credit(candidate,20)
        real_replace=os.replace
        def failed_replace(src,dst):
            if Path(dst)==store.path:raise OSError('disk full')
            return real_replace(src,dst)
        for name,kwargs in [('replace',{'side_effect':failed_replace}),('fsync',{'side_effect':OSError('permission denied')})]:
            with self.subTest(failure=name),patch('pesca_save.os.'+name,**kwargs):
                with self.assertRaises(SaveError):store.save(candidate)
            self.assertEqual(store.path.read_bytes(),before);self.assertEqual(state['ultimo_salvo'],stamp)
            self.assertEqual(store.last_good,state)
        with patch('pesca_save.json.dumps',side_effect=ValueError('serialization interrupted')):
            with self.assertRaises(SaveError):store.save(candidate)
        self.assertEqual(store.path.read_bytes(),before)
        store.save(candidate);self.assertEqual(store.backup_path.read_bytes(),before)
        self.assertFalse(list(store.path.parent.glob(store.path.name+'.*.tmp')))

    def test_F1_explicit_recovery_preserves_rejected(self):
        store=self.store('recovery');s=store.load(game.ESTADO_PADRAO);store.save(s);credit(s,100);store.save(s)
        rejected=b'{broken save';store.path.write_bytes(rejected)
        with self.assertRaises(SaveError):store.load(game.ESTADO_PADRAO)
        self.assertEqual(store.path.read_bytes(),rejected);self.assertTrue(store.backup_available(game.ESTADO_PADRAO))
        restored=store.recover(game.ESTADO_PADRAO);self.assertEqual(restored['moedas_centavos'],0)
        self.assertEqual(next(store.path.parent.glob('recovery.rejeitado-*.json')).read_bytes(),rejected)
        self.assertEqual(store.load(game.ESTADO_PADRAO),restored)

    def test_F2_two_processes_alias_and_separate_profiles(self):
        store=self.store('concurrent');env=os.environ.copy();env['PYTHONPATH']=str(ROOT)
        code="from pesca_save import SaveStore,SaveError; import sys\ntry:\n s=SaveStore(sys.argv[1]);s.close();print('open')\nexcept SaveError:print('blocked')"
        alias=store.path.parent/'alias'/'..'/store.path.name
        (store.path.parent/'alias').mkdir(exist_ok=True)
        for path in (store.path,alias):
            result=subprocess.run([sys.executable,'-c',code,str(path)],env=env,text=True,capture_output=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),'blocked')
        other=subprocess.run([sys.executable,'-c',code,str(store.path.parent/'other.json')],env=env,text=True,capture_output=True,timeout=20)
        self.assertEqual(other.stdout.strip(),'open');store.close()
        after=subprocess.run([sys.executable,'-c',code,str(store.path)],env=env,text=True,capture_output=True,timeout=20)
        self.assertEqual(after.stdout.strip(),'open')

    def test_F2_lock_released_after_crash(self):
        path=Path(PROFILE.name)/'crash.json';env=os.environ.copy();env['PYTHONPATH']=str(ROOT)
        process=subprocess.Popen([sys.executable,'-c',"from pesca_save import SaveStore;import sys;s=SaveStore(sys.argv[1]);print('ready',flush=True);sys.stdin.read()",str(path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
        try:
            self.assertEqual(process.stdout.readline().strip(),'ready')
            with self.assertRaises(SaveError):SaveStore(path)
        finally:
            process.terminate();process.communicate(timeout=20)
        with SaveStore(path):pass

    def test_F3_residual_simulation_and_offline(self):
        s=self.fresh();engine=FishingEngine(s)
        def wait():engine.state['pesca']={'etapa':'aguardando','restante':10.0}
        engine.wait=wait;wait();engine.advance(120,1800000000,0)
        self.assertEqual(len(engine.events),10);self.assertEqual(engine.state['pesca']['restante'],5)
        s=self.fresh();offline,report=replay(s,1800000000+20000)
        self.assertEqual(report['paid_seconds'],14400)
        again,r=replay(offline,1800000000+20000);self.assertEqual(r['count'],0)
        self.assertEqual(again['moedas_centavos'],offline['moedas_centavos'])

    def test_F5_exact_amount_and_legacy_drift(self):
        s=self.fresh()
        for _ in range(150):credit(s,cents(.2))
        self.assertEqual(s['moedas_centavos'],3000);self.assertTrue(can_buy(s,30));self.assertTrue(debit(s,30));self.assertEqual(s['moedas_centavos'],0)
        for version in (1,2):
            legacy={'schema_version':version,'moedas':sum([.2]*150)}
            migrated=migrate(legacy,game.ESTADO_PADRAO,1800000000)
            self.assertEqual(migrated['moedas_centavos'],3000);self.assertTrue(debit(migrated,30))
        self.assertEqual(reward(.15,1),18);self.assertEqual(reward(.125,0),12)
        store=self.store('money');store.save(s);payload=json.loads(store.path.read_text())
        self.assertNotIn('moedas',payload);self.assertEqual(payload['schema_version'],3)
        self.assertEqual(store.load(game.ESTADO_PADRAO)['moedas_centavos'],0)

    def test_malformed_profiles_rejected(self):
        invalids=[{'equipados':None},{'cosmeticos':None},{'moedas':float('nan')},{'moedas':-1},{'vara':True},{'barco':11},{'inventario':{'Lambari':-1}},{'inventario_por_id':{'lambari':'many'}},{'equipados':{'chapeu':'martelo_pesado'}},{'equipados':{'chapeu':'chapeu_coroa'}},{'pausado':'yes'},{'conquistas':[None]}]
        for raw in invalids:
            with self.subTest(raw=raw),self.assertRaises(SaveError):migrate(raw,game.ESTADO_PADRAO,1800000000)

    def test_migration_idempotent_and_fields_preserved(self):
        legacy={'moedas':12.34,'cosmeticos':['chapeu_pikachu'],'conquistas':['rei_pesca'],'inventario':{'Lambari':3},'future_field':{'untouched':True}}
        s=migrate(legacy,game.ESTADO_PADRAO,1800000000)
        self.assertEqual(migrate(s,game.ESTADO_PADRAO,1800000000),s)
        self.assertIn('chapeu_pikachu',s['cosmeticos']);self.assertIn('rei_pesca',s['conquistas'])
        self.assertEqual(s['registros_regionais'],{});self.assertEqual(s['future_field'],legacy['future_field'])

    def test_fashionista_without_reward_and_after_last_purchase(self):
        s=self.fresh();items=sold_items()
        s['cosmeticos']+=[i[0] for i in items[:-1]]
        self.assertNotIn('fashionista',s['conquistas']);self.assertEqual(len(fashionista_progress(s)['missing']),1)
        grant(s,CATALOGO);self.assertNotIn('fashionista',s['conquistas'])
        s['cosmeticos'].append(items[-1][0]);titles=grant(s,CATALOGO)
        self.assertIn('Fashionista',titles);self.assertNotIn('enciclopedia_viva',s['cosmeticos'])
        self.assertEqual(grant(s,CATALOGO),[]);self.assertEqual(fashionista_progress(s)['missing'],[])

    def test_F4_F6_F7_real_widgets(self):
        g=game.JogoPesca();g.setAttribute(Qt.WA_DontShowOnScreen,True)
        try:
            from pesca_viagens_ui import ColecaoDialog
            initial=len(g.findChildren(QDialog))
            for _ in range(50):
                d=ColecaoDialog(g);d.accept();self.assertFalse(d.timer.isActive());d.deleteLater()
                shop=game.LojaDialog(g);shop.accept();self.assertFalse(shop.timer.isActive());shop.deleteLater()
                APP.sendPostedEvents(None,QEvent.DeferredDelete)
            self.assertEqual(len(g.findChildren(QDialog)),initial)
            g.popup=None;g._popup_queue=[]
            titles=['Fashionista','Eu escolho você!','Mostre-me seu Coração Valente']
            for title in titles:g.mostrar_popup('Conquista desbloqueada: '+title)
            for i in range(100):g.mostrar_popup('Captura '+str(i))
            messages=[g.popup,*g._popup_queue]
            for title in titles:self.assertIn('Conquista desbloqueada: '+title,[m[0] for m in messages])
            with patch.object(g,'salvar',return_value=False),patch.object(QMessageBox,'warning'):
                from PySide6.QtGui import QCloseEvent
                event=QCloseEvent();g.closeEvent(event);self.assertFalse(event.isAccepted());self.assertFalse(g._closed)
        finally:g.close();g.deleteLater();APP.sendPostedEvents(None,QEvent.DeferredDelete)
        self.assertIsNone(g._store.lock)

    def test_F7_last_catch_upgrade_and_purchase_flows(self):
        from pesca_catalogo import ESPECIES,desbloquear
        from pesca_loja import SLOTS
        clock={'wall':1800000000.,'mono':0.}
        with patch.object(game,'SAVE_PATH',Path(PROFILE.name)/'achievement-flows.json'):
            g=game.JogoPesca(wall_clock=lambda:clock['wall'],monotonic_clock=lambda:clock['mono'])
        g.setAttribute(Qt.WA_DontShowOnScreen,True)
        def messages():return [x[0] for x in ([g.popup] if g.popup else [])+g._popup_queue]
        def clear():g.popup=None;g._popup_queue=[]
        try:
            candidate=copy.deepcopy(g.estado);candidate['conquistas']=[]
            candidate['inventario_por_id']={id_:1 for id_ in ESPECIES if id_!='lambari'}
            engine=FishingEngine(candidate)
            with patch.object(engine.rng,'choices',return_value=['lambari']):engine.begin_strike(clock['wall'],0)
            self.assertTrue(g._commit(engine.advance(0,clock['wall'],0)));clear()
            clock['wall']+=2;clock['mono']+=2;g.tick()
            self.assertIn('rei_pesca',g.estado['conquistas']);self.assertIn('colecao_expansao_88',g.estado['conquistas'])
            self.assertTrue(any(x.startswith('Captura:') for x in messages()))
            self.assertIn('Conquista desbloqueada: Rei da pesca.',messages())
            self.assertIn('Conquista desbloqueada: Explorador das oito águas',messages())
            candidate=copy.deepcopy(g.estado);candidate['vara']=9;candidate['pecas_vara']=10
            set_balance(candidate,100000);self.assertTrue(g._commit(candidate));clear()
            g.comprar_peca('vara');self.assertEqual(g.estado['vara'],10)
            self.assertIn('Conquista desbloqueada: Mestre da vara.',messages())
            self.assertTrue(any(x.startswith('Vara melhorada!') for x in messages()))
            items=sold_items();last=items[-1];candidate=copy.deepcopy(g.estado)
            candidate['cosmeticos']=list(dict.fromkeys([*game.ESTADO_PADRAO['cosmeticos'],*(x[0] for x in items[:-1])]))
            candidate['conquistas']=[x for x in candidate['conquistas'] if x!='fashionista']
            self.assertTrue(g._commit(candidate));clear();shop=game.LojaDialog(g)
            shop.abas.setCurrentIndex(1+list(SLOTS).index(last[1]));lst=shop.listas[last[1]]
            for row in range(lst.count()):
                if lst.item(row).data(Qt.UserRole)==last[0]:lst.setCurrentRow(row);break
            shop.btn.click();self.assertIn('fashionista',g.estado['conquistas'])
            self.assertNotIn('enciclopedia_viva',g.estado['cosmeticos'])
            self.assertIn('Conquista desbloqueada: Fashionista',messages())
            shop.accept();shop.deleteLater()
            persisted=g._store.load(game.ESTADO_PADRAO,clock['wall'])
            self.assertTrue({'rei_pesca','colecao_expansao_88','mestre_vara','fashionista'}<=set(persisted['conquistas']))
        finally:g.close();g.deleteLater();APP.sendPostedEvents(None,QEvent.DeferredDelete)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Audit))
    out=Path(os.environ.get('PESCA_IDLE_QA_DIR',PROFILE.name));out.mkdir(parents=True,exist_ok=True)
    (out/'audit.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'schema':SCHEMA,'profile_isolated':True,'python':sys.version},indent=2),encoding='utf-8')
    PROFILE.cleanup();raise SystemExit(0 if result.wasSuccessful() else 1)
