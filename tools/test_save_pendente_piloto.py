"""Pending-ID regression: synthetic files bounded inside the pilot checkout."""
import copy
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'qa' / 'save-pendente'
QA.mkdir(parents=True, exist_ok=True)
os.environ.update(PESCA_IDLE_SAVE_PATH=str(QA / 'guard.json'),
                  APPDATA=str(QA / 'appdata'), LOCALAPPDATA=str(QA / 'localappdata'),
                  TEMP=str(QA), TMP=str(QA), QT_QPA_PLATFORM='offscreen')
sys.path.insert(0, str(ROOT))

from pesca_idle import ESTADO_PADRAO
from pesca_save import SaveError, SaveStore, migrate
from pesca_pescaria import FishingEngine

NOW = 1792411200


def pending_state(profile='synthetic-pending'):
    state = migrate({}, ESTADO_PADRAO, NOW)
    state.update(perfil_id=profile, rng_state=random.Random(0).getstate())
    engine = FishingEngine(state)
    engine.begin_strike(NOW, 0)
    return engine.advance(0, NOW, 0)


class PendingIdTests(unittest.TestCase):
    def rejected_file_unchanged(self, state):
        with tempfile.TemporaryDirectory(dir=QA) as folder:
            path = Path(folder) / 'save.json'
            payload = json.dumps(state, ensure_ascii=False, indent=3).encode('utf-8')
            path.write_bytes(payload)
            backup = path.with_suffix('.json.bak')
            backup.write_bytes(b'synthetic-backup-sentinel')
            with SaveStore(path) as store:
                with self.assertRaisesRegex(SaveError, 'fisgada'):
                    store.load(ESTADO_PADRAO, NOW)
                self.assertIsNone(store.last_good)
                self.assertIsNone(store.last_bytes)
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(backup.read_bytes(), b'synthetic-backup-sentinel')
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()),
                             ['save.json', 'save.json.bak', 'save.json.lock'])

    def test_nonnumeric_suffix_reproduced(self):
        state = pending_state()
        state['pesca_pendente']['id'] = state['perfil_id'] + ':nao-numerico'
        self.rejected_file_unchanged(state)

    def test_invalid_suffix_variants(self):
        for suffix in ('', 'abc', '1x', '1:2', '-1', '+1', '1.0', ' 1', '1 ', '\n1', '١', '0', '2', '9' * 5000):
            with self.subTest(suffix=suffix[:24]):
                state = pending_state()
                state['pesca_pendente']['id'] = state['perfil_id'] + ':' + suffix
                self.rejected_file_unchanged(state)

    def test_invalid_prefix_and_types(self):
        for value in ('different-profile:1', None, 1, [], {}):
            with self.subTest(value=value):
                state = pending_state()
                state['pesca_pendente']['id'] = value
                self.rejected_file_unchanged(state)

    def test_legacy_invalid_pending_is_not_migrated_or_backed_up(self):
        state = pending_state()
        state['schema_version'] = 3
        state.pop('pilot_kind')
        state.pop('medidas_peixes')
        state['pesca_pendente']['id'] = state['perfil_id'] + ':invalid'
        self.rejected_file_unchanged(state)

    def test_valid_ids_load_deliver_and_roundtrip(self):
        for profile, suffix in (('synthetic-pending', '1'), ('synthetic:with:colons', '1'),
                                ('synthetic-leading-zero', '0001')):
            with self.subTest(profile=profile):
                state = pending_state(profile)
                state['pesca_pendente']['id'] = profile + ':' + suffix
                with tempfile.TemporaryDirectory(dir=QA) as folder:
                    path = Path(folder) / 'save.json'
                    payload = json.dumps(state).encode('utf-8')
                    path.write_bytes(payload)
                    with SaveStore(path) as store:
                        loaded = store.load(ESTADO_PADRAO, NOW)
                        self.assertEqual(path.read_bytes(), payload)
                        engine = FishingEngine(loaded)
                        engine.finish_strike()
                        result = engine.advance(0, NOW, 0)
                        self.assertEqual(len(engine.events), 1)
                        self.assertEqual(result['medidas_peixes']['quantity'], 1)
                        store.save(result)
                    with SaveStore(path) as store:
                        again = store.load(ESTADO_PADRAO, NOW)
                    self.assertEqual(again['medidas_peixes'], result['medidas_peixes'])
                    self.assertEqual(again['moedas_centavos'], result['moedas_centavos'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
