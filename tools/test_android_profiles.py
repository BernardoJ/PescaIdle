"""Private-path/save contracts with synthetic QStandardPaths; not native Android QA."""
import argparse
import ast
import copy
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pesca_piloto as profiles
from pesca_save import SaveStore, SaveError, migrate
from pesca_moedas import set_cents
from pesca_pescaria import FishingEngine
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication

TREE = ast.parse((ROOT/'pesca_idle.py').read_text(encoding='utf-8'))
DEFAULTS = next(ast.literal_eval(n.value) for n in TREE.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='ESTADO_PADRAO' for t in n.targets))
NOW = 1793116800


class NativeApp:
    def platformName(self): return 'android'


class AndroidProfiles(unittest.TestCase):
    def setUp(self):
        qa=ROOT/'qa';qa.mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(prefix='android-profile-', dir=qa)
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.private=self.folder/'br.com.bernardoj.pescaidle'/'files'
        self.cache=self.folder/'br.com.bernardoj.pescaidle.qa'/'cache'
        self.old_root=profiles._android_root
        self.addCleanup(setattr,profiles,'_android_root',self.old_root)
        profiles._android_root=None
        self.env=patch.dict(os.environ, {}, clear=False);self.env.start();self.addCleanup(self.env.stop)
        os.environ.pop('PESCA_IDLE_SAVE_PATH',None);os.environ.pop('PESCA_IDLE_QA_DIR',None)
        self.locations={QStandardPaths.AppDataLocation:str(self.private),QStandardPaths.CacheLocation:str(self.cache)}

    def bootstrap(self,qa=False):
        with patch.object(QApplication,'instance',return_value=NativeApp()), \
             patch.object(QStandardPaths,'writableLocation',side_effect=self.locations.__getitem__):
            return profiles.prepare_android_profile(qa)

    def state(self):
        s=migrate({},DEFAULTS,NOW);s['rng_state']=random.Random(71).getstate()
        return s

    def test_desktop_default_and_boundary_unchanged(self):
        os.environ['PESCA_IDLE_MOBILE']='1';os.environ['PESCA_IDLE_ANDROID_QA']='1'
        os.environ['PESCA_IDLE_ANDROID_ROOT']=str(self.folder/'untrusted')
        self.assertEqual(profiles.prepare_profile(),ROOT/'perfil-piloto'/'save.json')
        self.assertEqual(profiles.validate_profile_path(ROOT/'qa'/'synthetic.json'),ROOT/'qa'/'synthetic.json')
        with self.assertRaises(ValueError):profiles.validate_profile_path(self.folder.parent.parent.parent/'outside.json')

    def test_native_bootstrap_required(self):
        with patch.object(QApplication,'instance',return_value=None):
            with self.assertRaises(ValueError):profiles.prepare_android_profile()
        self.assertIsNone(profiles._android_root)
        self.assertFalse(self.private.exists())

    def test_missing_or_relative_private_root_rejected(self):
        for value in ('','relative/private'):
            self.locations[QStandardPaths.AppDataLocation]=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.bootstrap()
        self.assertIsNone(profiles._android_root)

    def test_private_pilot_selected_before_game_import(self):
        path=self.bootstrap()
        self.assertEqual(path,self.private/'pilotos'/'tamanhos-v1'/'save.json')
        self.assertEqual(profiles.prepare_profile(),path)
        self.assertEqual(profiles._android_root,path.parent)
        self.assertFalse(path.exists())

    def test_legacy_root_save_is_never_read_or_migrated(self):
        self.private.mkdir(parents=True);legacy=self.private/'save.json'
        legacy.write_bytes(b'synthetic legacy sentinel; never read')
        path=self.bootstrap()
        with SaveStore(path) as store:
            s=store.load(DEFAULTS,NOW);store.save(s)
        self.assertEqual(legacy.read_bytes(),b'synthetic legacy sentinel; never read')
        self.assertNotEqual(path,legacy)
        self.assertFalse(list(self.private.glob('save.pre-*.json')))

    def test_private_override_cannot_escape_or_select_other_pilot(self):
        for path in (self.private/'save.json',self.private/'pilotos'/'other'/'save.json',ROOT/'perfil-piloto'/'save.json',self.cache/'qa-tamanhos-v1'/'save.json'):
            with self.subTest(path=str(path)):
                os.environ['PESCA_IDLE_SAVE_PATH']=str(path)
                with self.assertRaises(ValueError):self.bootstrap()
                self.assertIsNone(profiles._android_root)
        self.assertFalse(self.private.exists())

    def test_path_traversal_rejected_by_active_context(self):
        p=self.bootstrap()
        for path in (p.parent/'..'/'other'/'save.json',self.private/'save.json',ROOT/'qa'/'other.json',p.parent):
            with self.subTest(path=str(path)),self.assertRaises(ValueError):profiles.validate_profile_path(path)

    def test_symlink_to_other_context_rejected(self):
        path=self.bootstrap();outside=self.private/'other';outside.mkdir()
        link=path.parent/'redirect'
        try:link.symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('Symlink creation not available')
        with self.assertRaises(ValueError):profiles.validate_profile_path(link/'save.json')
        self.assertFalse((outside/'save.json').exists())

    def test_symlink_pilot_directory_rejected_before_open(self):
        self.private.mkdir(parents=True);other=self.private/'other';other.mkdir()
        (self.private/'pilotos').symlink_to(other,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'redirecionado'):self.bootstrap()
        self.assertIsNone(profiles._android_root)
        self.assertFalse((other/'tamanhos-v1').exists())

    def test_qa_is_separate_stable_private_context(self):
        production=self.bootstrap();os.environ.pop('PESCA_IDLE_SAVE_PATH')
        qa=self.bootstrap(qa=True)
        self.assertEqual(qa,self.cache/'qa-tamanhos-v1'/'save.json')
        self.assertEqual(Path(os.environ['PESCA_IDLE_QA_DIR']),qa.parent)
        self.assertEqual(self.bootstrap(qa=True),qa)
        with self.assertRaises(ValueError):profiles.validate_profile_path(production)
        os.environ.pop('PESCA_IDLE_SAVE_PATH');self.bootstrap()
        with self.assertRaises(ValueError):profiles.validate_profile_path(qa)

    def test_production_package_cannot_claim_qa_context(self):
        self.locations[QStandardPaths.CacheLocation]=str(self.private/'cache')
        with self.assertRaisesRegex(ValueError,'pacote'):self.bootstrap(qa=True)
        self.assertIsNone(profiles._android_root)

    def test_new_save_close_reopen_preserves_snapshot(self):
        path=self.bootstrap()
        with SaveStore(path) as store:
            s=store.load(DEFAULTS,NOW);set_cents(s,12345);store.save(s)
        original=path.read_bytes()
        # Simulates a new bootstrap; production context is stable after updates.
        profiles._android_root=None
        self.assertEqual(self.bootstrap(),path)
        with SaveStore(path) as store:
            loaded=store.load(DEFAULTS,NOW+200)
        self.assertEqual(loaded['moedas_centavos'],12345)
        self.assertEqual(loaded['perfil_id'],s['perfil_id'])
        self.assertEqual(loaded['clima'],s['clima'])
        self.assertEqual(path.read_bytes(),original)

    def test_lock_is_exclusive_and_released(self):
        path=self.bootstrap()
        with SaveStore(path) as store:
            with self.assertRaises(SaveError):SaveStore(path)
        with SaveStore(path):pass

    def test_corrupted_save_and_backups_preserved(self):
        path=self.bootstrap();path.write_bytes(b'{synthetic broken JSON')
        backup=path.with_suffix('.json.bak');backup.write_bytes(b'backup sentinel')
        with SaveStore(path) as store:
            with self.assertRaises(SaveError):store.load(DEFAULTS,NOW)
            self.assertFalse(store.backup_available(DEFAULTS,NOW))
        self.assertEqual(path.read_bytes(),b'{synthetic broken JSON')
        self.assertEqual(backup.read_bytes(),b'backup sentinel')

    def test_schema5_without_climate_rejected_on_private_path(self):
        path=self.bootstrap();s=self.state();s.pop('clima')
        payload=json.dumps(s).encode();path.write_bytes(payload)
        expanded=migrate({},DEFAULTS,NOW-10)
        with SaveStore(path) as store:
            with self.assertRaisesRegex(SaveError,'clima'):store.load(expanded,NOW)
        self.assertEqual(path.read_bytes(),payload)
        self.assertFalse(path.with_suffix('.json.bak').exists())

    def test_schema4_upgrade_backup_exact_and_reopen_idempotent(self):
        path=self.bootstrap();s=self.state();s['schema_version']=4;s.pop('clima')
        payload=json.dumps(s,indent=3).encode();path.write_bytes(payload)
        with SaveStore(path) as store:
            loaded=store.load(DEFAULTS,NOW)
        self.assertEqual((path.parent/'save.pre-schema-4.json').read_bytes(),payload)
        stable=path.read_bytes()
        profiles._android_root=None;self.bootstrap()
        with SaveStore(path) as store:
            again=store.load(DEFAULTS,NOW+1000)
        self.assertEqual(again['clima'],loaded['clima'])
        self.assertEqual(path.read_bytes(),stable)

    def test_native_smoke_restart_marker_verifies_snapshot_before_game(self):
        from tools.android_smoke import snapshot_digest,read_reopen_snapshot
        path=self.bootstrap(qa=True);s=self.state();s['pausado']=True
        digest=snapshot_digest(s)
        s['android_qa_reopen']={'version':1,'sha256':digest}
        with SaveStore(path) as store:store.save(s)
        reopened=read_reopen_snapshot(DEFAULTS)
        self.assertEqual(reopened['android_qa_reopen']['sha256'],digest)
        # Intentional pause advances the watermark during real background/resume.
        reopened['ultimo_processado_utc']+=120
        self.assertEqual(snapshot_digest(reopened),digest)
        with SaveStore(path) as store:store.save(reopened)
        self.assertEqual(read_reopen_snapshot(DEFAULTS)['perfil_id'],s['perfil_id'])

    def test_native_smoke_restart_marker_detects_corrupt_ledger(self):
        from tools.android_smoke import snapshot_digest,read_reopen_snapshot
        path=self.bootstrap(qa=True);s=self.state()
        s['android_qa_reopen']={'version':1,'sha256':snapshot_digest(s)}
        set_cents(s,99999)
        with SaveStore(path) as store:store.save(s)
        original=path.read_bytes()
        with self.assertRaisesRegex(RuntimeError,'snapshot'):read_reopen_snapshot(DEFAULTS)
        self.assertEqual(path.read_bytes(),original)

    def foreign_profile(self):
        foreign=self.private/'pilotos'/'other-synthetic'/'save.json'
        foreign.parent.mkdir(parents=True,exist_ok=True)
        foreign.write_text(json.dumps(self.state()),encoding='utf-8')
        return foreign

    def test_auxiliary_backup_cannot_import_another_private_context(self):
        path=self.bootstrap();foreign=self.foreign_profile();foreign_bytes=foreign.read_bytes()
        path.write_bytes(b'{synthetic rejected current save')
        original=path.read_bytes()
        with SaveStore(path) as store:
            store.backup_path.symlink_to(foreign)
            self.assertFalse(store.backup_available(DEFAULTS,NOW))
            with self.assertRaisesRegex(SaveError,'contexto'):store.recover(DEFAULTS,NOW)
            self.assertTrue(store.backup_path.is_symlink())
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(foreign.read_bytes(),foreign_bytes)
        self.assertFalse(list(path.parent.glob('save.rejeitado-*.json')))

    def test_migration_backup_symlinks_rejected_without_cross_context_read(self):
        path=self.bootstrap();foreign=self.foreign_profile();foreign_bytes=foreign.read_bytes()
        for version in (1,2,3,4):
            with self.subTest(version=version):
                current=path.parent/('version-'+str(version))/'save.json';current.parent.mkdir()
                state=self.state();state['schema_version']=version
                if version<4:state.pop('pilot_kind');state.pop('medidas_peixes')
                state.pop('clima');payload=json.dumps(state).encode();current.write_bytes(payload)
                suffix='.pre-expansao-v1.json' if version==1 else '.pre-schema-'+str(version)+'.json'
                backup=current.with_name(current.stem+suffix);backup.symlink_to(foreign)
                with SaveStore(current) as store:
                    with self.assertRaisesRegex(SaveError,'contexto'):store.load(DEFAULTS,NOW)
                self.assertEqual(current.read_bytes(),payload)
                self.assertTrue(backup.is_symlink())
                self.assertEqual(foreign.read_bytes(),foreign_bytes)
                self.assertFalse(current.with_suffix('.json.bak').exists())
                self.assertFalse(list(current.parent.glob('*.tmp')))

    def test_atomic_backup_destination_escape_is_rejected_before_replace(self):
        path=self.bootstrap();foreign=self.foreign_profile();foreign_bytes=foreign.read_bytes()
        with SaveStore(path) as store:
            state=store.load(DEFAULTS,NOW);store.save(state);original=path.read_bytes()
            store.backup_path.symlink_to(foreign)
            changed=copy.deepcopy(state);set_cents(changed,98765)
            with self.assertRaisesRegex(SaveError,'contexto'):store.save(changed)
            self.assertTrue(store.backup_path.is_symlink())
            self.assertEqual(path.read_bytes(),original)
        self.assertEqual(foreign.read_bytes(),foreign_bytes)
        self.assertFalse(list(path.parent.glob('*.tmp')))

    def test_lock_symlink_cannot_touch_another_private_context(self):
        path=self.bootstrap();foreign=self.foreign_profile();foreign_bytes=foreign.read_bytes()
        path.with_suffix('.json.lock').symlink_to(foreign)
        with self.assertRaisesRegex(SaveError,'contexto'):SaveStore(path)
        self.assertEqual(foreign.read_bytes(),foreign_bytes)
        self.assertFalse(path.exists())

    def test_main_path_redirect_after_lock_is_rejected_on_load(self):
        path=self.bootstrap();foreign=self.foreign_profile();foreign_bytes=foreign.read_bytes()
        with SaveStore(path) as store:
            path.symlink_to(foreign)
            with self.assertRaisesRegex(SaveError,'contexto'):store.load(DEFAULTS,NOW)
        self.assertTrue(path.is_symlink())
        self.assertEqual(foreign.read_bytes(),foreign_bytes)

    def test_pending_capture_preserved_across_private_save_reload(self):
        path=self.bootstrap();engine=FishingEngine(self.state());pending=copy.deepcopy(engine.begin_strike(NOW,0))
        state=engine.advance(0,NOW,0)
        with SaveStore(path) as store:store.save(state)
        with SaveStore(path) as store:loaded=store.load(DEFAULTS,NOW+100)
        self.assertEqual(loaded['pesca_pendente'],json.loads(json.dumps(pending)))
        replay=FishingEngine(loaded);replay.advance(1.5,NOW+100,0)
        self.assertEqual(len(replay.events),1)
        self.assertEqual(replay.state['moedas_centavos'],pending['gain_cents'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve()
    if not out.is_relative_to(ROOT/'qa') or out==ROOT/'qa':parser.error('Use nova pasta em qa do checkout.')
    out.mkdir(parents=True,exist_ok=False)
    with (out/'tests.log').open('w',encoding='utf-8') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AndroidProfiles))
    summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                 synthetic_only=True,native_android=False,scope='QStandardPaths simulated; SaveStore real; native APK must also pass emulator checks.')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary));return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
