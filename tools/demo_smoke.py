"""Two-process frozen/source demo smoke; called only by the explicit demo entry."""
import copy
import json
from pathlib import Path
import sys
import traceback


def execute(app, game, panel, output):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from tools.demo_tamanhos import read_fixture
    from pesca_museu_ui import MuseuDialog
    from pesca_tamanhos import exhibit
    mode = sys.argv[sys.argv.index('--demo-smoke')+1]
    try:
        if mode not in ('capture','reopen'):
            raise ValueError('Use capture ou reopen.')
        output.mkdir(parents=True,exist_ok=True)
        result_path = output / (mode+'.json')
        if result_path.exists():
            raise ValueError('Saída do smoke já existe; use uma pasta nova.')
        if mode=='capture':
            if game.estado['demo_tamanhos']['next_step']!=0:
                raise ValueError('Smoke capture exige um perfil sintético novo.')
            for index,step in enumerate(read_fixture()['steps']):
                QTest.mouseClick(panel.capture,Qt.LeftButton)
                app.processEvents()
                if (game.estado['demo_tamanhos']['next_step']!=index+1
                        or game._last_result['size_news']!=step['expected_news']):
                    raise ValueError('Captura de demonstração divergiu.')
            QTest.mouseClick(panel.museum_button,Qt.LeftButton)
            app.processEvents()
            museum=panel.museum
            museum.setAttribute(Qt.WA_DontShowOnScreen,True)
            for slot in (0,2):
                museum.specimen_selectors[slot].setFocus()
                QTest.keyClick(museum.specimen_selectors[slot],Qt.Key_End)
            app.processEvents()
            game.timer_save.timeout.emit()
            if game._save_error:raise ValueError(game._save_error)
            expected={k:copy.deepcopy(game.estado[k]) for k in
                      ('moedas_centavos','inventario_por_id','medidas_peixes','museu','conquistas','demo_tamanhos')}
            museum.accept()
            result={'ok':True,'frozen':bool(getattr(sys,'frozen',False)),
                    'identification':game.demo_info,'expected':expected}
        else:
            previous=json.loads((output/'capture.json').read_text(encoding='utf-8'))
            for key,value in previous['expected'].items():
                if game.estado[key]!=value:raise ValueError('Reabertura mudou: '+key)
            if not game.pausado or game.estado['pesca_pendente'] is not None:
                raise ValueError('Demonstração retomou pesca ou criou pendente.')
            museum=MuseuDialog(game)
            museum.setAttribute(Qt.WA_DontShowOnScreen,True)
            museum.show();app.processEvents()
            if exhibit(game.estado,0)['mm']!=40:
                raise ValueError('Exemplar menor não foi preservado.')
            museum.grab().save(str(output/'exe-museu-reaberto.png'))
            museum.accept()
            result={'ok':True,'frozen':bool(getattr(sys,'frozen',False)),
                    'identification':game.demo_info,'same_records_choices_inventory_money_awards':True,
                    'count':game.estado['medidas_peixes']['quantity'],
                    'choices':game.estado['museu']['exemplares']}
        if not game.close() or not game._closed:
            raise ValueError('Encerramento não confirmado.')
        result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        app.exit(0)
    except (ValueError,OSError,KeyError,IndexError) as exc:
        output.mkdir(parents=True,exist_ok=True)
        (output/(mode+'-failure.txt')).write_text(traceback.format_exc(),encoding='utf-8')
        app.exit(1)
