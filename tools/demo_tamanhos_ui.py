"""Demo-only controls feeding synthetic pending events into the real engine."""
import copy
from datetime import datetime

from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QMenu, QSizePolicy

from tools.demo_tamanhos import ROOT, read_fixture, identification
from pesca_idle import JogoPesca
from pesca_pescaria import FishingEngine
from pesca_tempo import snapshot
from pesca_catalogo import ESPECIES, VERSION
from pesca_moedas import reward
from pesca_museu import change_exhibit
from pesca_tamanhos import rule_snapshot, band
from pesca_conquistas import grant
from pesca_loja import CATALOGO


def demo_now():
    return datetime.fromisoformat(read_fixture()['local_time']).timestamp()


class DemoGame(JogoPesca):
    def __init__(self):
        self.demo_clock = demo_now()
        self.demo_info = identification()
        super().__init__(wall_clock=lambda:self.demo_clock, monotonic_clock=lambda:0,
                         recovery_decision=lambda:False)
        self.pausado = True
        self.estado['pausado'] = True
        self.demo_clock = max(self.demo_clock, self.estado['ultimo_processado_utc'])
        self._preview_clock = datetime.fromisoformat(read_fixture()['local_time'])
        self.setWindowTitle('DEMONSTRAÇÃO — PescaIdle tamanhos')
        self.relogio.stop()  # Manual fixture actions; no background/parallel fishing.
        if self.estado['demo_tamanhos'].get('last_event'):
            self.present(self.estado['demo_tamanhos']['last_event'])

    def salvar(self):
        self.pausado = True
        self.estado['pausado'] = True
        return super().salvar()

    def abrir_menu(self):
        menu = QMenu(self)
        menu.addAction('Museu', self.abrir_museu)
        menu.addAction('Enciclopédia', self.abrir_enciclopedia)
        menu.addAction('Roteiro da demonstração', lambda:self.demo_panel.show())
        menu.addAction('Salvar e fechar demonstração', self.close)
        menu.exec(self.mapToGlobal(self.rect_icone.bottomLeft()))

    def present(self, event):
        self._last_result = copy.deepcopy(event)
        self.capturando = .6
        self.fisgando = 0
        self.popup = [self._describe(event)[0], '#ffe3ac', 60]
        self._popup_queue.clear()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setFont(QFont('Segoe UI', 9, QFont.Bold))
        badge = QRect(12, self.height()-55, min(250, self.width()-24), 19)
        painter.fillRect(badge, QColor('#1c2b3b'))
        painter.setPen(QColor('#ffe3ac'))
        painter.drawText(badge, Qt.AlignCenter, 'DEMONSTRAÇÃO · DADOS SINTÉTICOS')
        painter.end()

    def next_capture(self):
        self.pausado = True
        fixture = read_fixture()
        index = self.estado['demo_tamanhos']['next_step']
        if index >= len(fixture['steps']):
            return None
        step = fixture['steps'][index]
        state = copy.deepcopy(self.estado)
        engine = FishingEngine(state)
        if state['pesca_pendente'] is None:
            state = engine.state
            state['contador_eventos'] += 1
            rule = rule_snapshot(step['species_id'])
            context = snapshot(self.demo_clock)
            context.update(map_id='enseada_do_poente', vara=state['vara'], barco=state['barco'],
                           catalog_version=VERSION)
            gain = reward(ESPECIES[step['species_id']]['valor'], state['barco'])
            # Fixture construction only; delivery, records and money are NOT reimplemented.
            state['pesca_pendente'] = {
                'id':state['perfil_id']+':'+str(state['contador_eventos']),
                'species_id':step['species_id'], 'categoria':'peixe', 'context':context,
                'gain_cents':gain, 'gain':gain/100,
                'measurement':{'mm':step['mm'], 'band':band(step['mm'],rule), 'rule':rule}}
            state['pesca'] = {'etapa':'fisgando', 'restante':1.5}
            # Preserve the frozen result if the process closes before delivery.
            if not self._commit(engine.advance(0, self.demo_clock, context['offset_seconds'])):
                return None
            engine = FishingEngine(self.estado)
        context = engine.state['pesca_pendente']['context']
        candidate = engine.advance(1.5, self.demo_clock, context['offset_seconds'])
        if len(engine.events) != 1:
            raise ValueError('A captura sintética não foi entregue exatamente uma vez.')
        event = engine.events[0]
        if (event['species_id'] != step['species_id'] or event['measurement']['mm'] != step['mm']
                or event['size_news'] != step['expected_news']):
            raise ValueError('O cenário sintético divergiu do roteiro; perfil preservado.')
        candidate['ultimo_processado_utc'] = self.demo_clock + 1.5
        candidate['pausado'] = True
        candidate['demo_tamanhos'].update(next_step=index+1, last_event=copy.deepcopy(event))
        # Add each newly demonstrated species to an empty slot via the actual museum API.
        if event['species_id'] not in candidate['museu']['aquario'] and None in candidate['museu']['aquario']:
            slot = candidate['museu']['aquario'].index(None)
            candidate = change_exhibit(candidate, slot, event['species_id'])
        grant(candidate, CATALOGO)
        if not self._commit(candidate):
            return None
        self.demo_clock += 1.5
        self.present(event)
        return event


class DemoPanel(QDialog):
    def __init__(self, game, profile):
        super().__init__(game)
        self.game = game
        self.setWindowTitle('Demonstração de tamanhos — dados sintéticos')
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.resize(480, 550)
        self.setMinimumSize(280, 220)
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        body = QWidget()
        body.setObjectName('demoConteudo')
        body.setStyleSheet('#demoConteudo { background: #1c2b3b; }')
        layout = QVBoxLayout(body)
        scroll.setWidget(body)
        def label(text):
            item = QLabel(text)
            item.setTextFormat(Qt.PlainText)
            item.setWordWrap(True)
            item.setMinimumWidth(0)
            item.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            layout.addWidget(item)
            return item
        heading = label('DEMONSTRAÇÃO · Tamanhos e aquário')
        heading.setProperty('heading', True)
        info = game.demo_info
        label('Revisão '+info['source_commit'][:12]+' · snapshot '+info['source_snapshot'][:12])
        label('Capturas preparadas, não sorteios de uma partida normal. A pesca fica pausada. '
              'Cada clique entrega um exemplar pelo motor do jogo; não é necessário esperar.')
        self.status = label('')
        self.next_label = label('')
        self.capture = QPushButton()
        self.capture.clicked.connect(self.advance)
        layout.addWidget(self.capture)
        self.last = label('Nenhuma captura nesta demonstração. Você pode abrir o museu vazio.')
        self.museum_button = QPushButton('Abrir museu')
        self.museum_button.clicked.connect(self.open_museum)
        layout.addWidget(self.museum_button)
        encyclopedia = QPushButton('Abrir enciclopédia')
        encyclopedia.clicked.connect(game.abrir_enciclopedia)
        layout.addWidget(encyclopedia)
        label('Roteiro: acompanhe os quatro Lambaris, termine as dez capturas e compare os três espaços. '
              'Troque menor/maior no museu, feche e reabra este mesmo modo para conferir a persistência.')
        self.profile_label = label('Grava somente em: '+profile.relative_to(ROOT).as_posix()+
              '\nO perfil normal e o save em APPDATA não são usados. Para repetir do zero, use uma pasta nova de QA; não apague seu progresso normal.')
        self.exit_button = QPushButton('Salvar e fechar')
        self.exit_button.clicked.connect(game.close)
        layout.addWidget(self.exit_button)
        self.museum = None
        self.refresh()

    def refresh(self):
        fixture = read_fixture()
        index = self.game.estado['demo_tamanhos']['next_step']
        self.status.setText(f'{index}/{len(fixture["steps"])} capturas do roteiro concluídas')
        self.capture.setEnabled(index < len(fixture['steps']))
        self.capture.setText('Próxima captura' if index < len(fixture['steps']) else 'Roteiro concluído')
        self.next_label.setText('Próximo: '+fixture['steps'][index]['label'] if index < len(fixture['steps'])
                                else 'Compare os três espaços e escolha menor ou maior exemplar no museu.')
        event = self.game.estado['demo_tamanhos'].get('last_event')
        if event:
            self.last.setText(self.game._describe(event)[0])

    def advance(self):
        try:
            event = self.game.next_capture()
            self.refresh()
            if event is None and self.game._save_error:
                self.last.setText('Captura não salva: '+self.game._save_error)
        except ValueError as exc:
            self.last.setText(str(exc))
            self.capture.setEnabled(False)

    def open_museum(self):
        from pesca_museu_ui import MuseuDialog
        if self.museum is None:
            self.museum = MuseuDialog(self.game)
            self.museum.finished.connect(lambda *_:self.clear_museum())
        self.museum.show()
        self.museum.raise_()

    def clear_museum(self):
        if self.museum:
            self.museum.deleteLater()
        self.museum = None

    def closeEvent(self, event):
        if self.game.close():
            event.accept()
        else:
            event.ignore()
