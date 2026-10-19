"""Explicit synthetic demonstration. No product imports before profile isolation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from pesca_piloto import ROOT, validate_profile_path

RESOURCES = Path(getattr(sys, '_MEIPASS', ROOT))
FIXTURE = RESOURCES / 'tools/fixtures/demo_tamanhos.json'
KIND = 'demo-tamanhos-v1'


def prepare_environment():
    folder = validate_profile_path(os.getenv('PESCA_IDLE_DEMO_DIR', ROOT / 'perfil-demo-tamanhos'))
    # An override is QA-only. Never repurpose the ordinary pilot profile.
    if folder != ROOT / 'perfil-demo-tamanhos' and not folder.is_relative_to(ROOT / 'qa'):
        raise ValueError('Demonstração: use perfil-demo-tamanhos ou uma subpasta de qa neste candidato.')
    folder.mkdir(parents=True, exist_ok=True)
    for name in ('appdata', 'localappdata', 'tmp'):
        (folder / name).mkdir(exist_ok=True)
    path = validate_profile_path(folder / 'save.json')
    if path.parent != folder or path.name != 'save.json':
        raise ValueError('Demonstração: o save não pode redirecionar para outro perfil. Original preservado.')
    # Ignore any inherited ordinary save override, even before product imports.
    os.environ.update(PESCA_IDLE_SAVE_PATH=str(path),
        APPDATA=str(folder / 'appdata'), LOCALAPPDATA=str(folder / 'localappdata'),
        TEMP=str(folder / 'tmp'), TMP=str(folder / 'tmp'))
    if path.exists():
        raw = json.loads(path.read_text(encoding='utf-8-sig'))
        demo = raw.get('demo_tamanhos') if isinstance(raw, dict) else None
        fixture = read_fixture()
        if (not isinstance(demo, dict) or demo.get('kind') != KIND
                or type(demo.get('next_step')) is not int
                or not 0 <= demo['next_step'] <= len(fixture['steps'])):
            raise ValueError('Este arquivo não é um perfil válido da demonstração. Original preservado; escolha outra pasta de QA.')
    return path


def read_fixture():
    fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
    if fixture.get('version') != 1 or fixture.get('kind') != KIND or not fixture.get('steps'):
        raise ValueError('Fixture de demonstração inválida.')
    return fixture


def source_snapshot():
    names = [p for p in ROOT.glob('*.py')]
    names += [p for p in (ROOT / 'assets').rglob('*')
              if p.suffix in ('.png', '.json') and 'source' not in p.relative_to(ROOT / 'assets').parts]
    names += [ROOT / 'tools' / n for n in ('demo_tamanhos.py', 'demo_tamanhos_ui.py',
                                          'demo_smoke.py', 'fixtures/demo_tamanhos.json')]
    files = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(names) if p.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), files


def identification():
    if getattr(sys, 'frozen', False):
        return json.loads((RESOURCES / 'demo_build.json').read_text(encoding='utf-8'))
    snapshot, _ = source_snapshot()
    try:
        head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
            stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        head = 'fonte-local'
    return {'source_commit': head, 'source_snapshot': snapshot}


def initialize_profile(path, now):
    # All imports below are safe only after prepare_environment has selected a profile.
    if Path(os.environ.get('PESCA_IDLE_SAVE_PATH', '')).resolve() != path:
        raise ValueError('Configure o perfil da demonstração antes de inicializar.')
    from pesca_idle import ESTADO_PADRAO
    from pesca_save import SaveStore, migrate
    from pesca_tamanhos import empty_sizes
    import random
    if path.exists():
        return
    fixture = read_fixture()
    state = migrate({}, ESTADO_PADRAO, now)
    state.update(perfil_id='synthetic-demo-tamanhos-v1', pausado=True,
                 rng_state=random.Random(fixture['seed']).getstate(), ultimo_processado_utc=now)
    state['medidas_peixes'] = empty_sizes(state['perfil_id'])
    state['demo_tamanhos'] = {'kind': KIND, 'next_step': 0, 'last_event': None}
    with SaveStore(path) as store:
        store.save(state)


def run():
    try:
        path = prepare_environment()
        if '--demo-smoke' in sys.argv:
            if not os.getenv('PESCA_IDLE_DEMO_DIR') or not os.getenv('PESCA_IDLE_DEMO_QA_DIR'):
                raise ValueError('Smoke exige PESCA_IDLE_DEMO_DIR e PESCA_IDLE_DEMO_QA_DIR explícitos.')
            output = validate_profile_path(os.environ['PESCA_IDLE_DEMO_QA_DIR'])
            if not output.is_relative_to(ROOT / 'qa'):
                raise ValueError('Saída do smoke deve ficar dentro de qa deste candidato.')
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import QTimer, Qt
        from pesca_ui import configure_app
        from tools.demo_tamanhos_ui import DemoGame, DemoPanel, demo_now
        from pesca_save import SaveError
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        configure_app(app)
        try:
            initialize_profile(path, demo_now())
            game = DemoGame()
        except SaveError as exc:
            if '--demo-smoke' in sys.argv:
                print('Demonstração não iniciada: '+str(exc), file=sys.stderr)
            else:
                QMessageBox.critical(None, 'Perfil da demonstração rejeitado', str(exc))
            return 2
        panel = DemoPanel(game, path)
        game.demo_panel = panel
        if '--demo-smoke' in sys.argv:
            game.setAttribute(Qt.WA_DontShowOnScreen, True)
            panel.setAttribute(Qt.WA_DontShowOnScreen, True)
        game.show()
        panel.show()
        if '--demo-smoke' in sys.argv:
            from tools.demo_smoke import execute
            QTimer.singleShot(0, lambda: execute(app, game, panel, output))
        return app.exec()
    except (ValueError, OSError, KeyError) as exc:
        # No reset/recovery on demo errors. The file is left intact.
        if getattr(sys, 'frozen', False):
            from PySide6.QtWidgets import QApplication, QMessageBox
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, 'Demonstração não iniciada', str(exc))
        else:
            print('Demonstração não iniciada: '+str(exc), file=sys.stderr)
        return 2
