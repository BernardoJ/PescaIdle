"""A single, bounded pixel aquarium and a discovery-based exhibit editor."""
import math
from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPoint
from PySide6.QtGui import QImage, QPainter, QColor, QPolygon, QPixmap, QIcon
from PySide6.QtWidgets import (QApplication, QDialog, QWidget, QVBoxLayout,
    QHBoxLayout, QScrollArea, QLabel, QPushButton, QComboBox, QSizePolicy, QScroller)
from pesca_catalogo import ESPECIES
from pesca_especies_visual import species_image
from pesca_museu import CAPACIDADE, eligible_species, slot_status, change_exhibit
from pesca_plataforma import mobile
from pesca_tamanhos import exhibit, fmt as fmt_length
from pesca_tamanho_visual import scale_for
from pesca_museu_visual import draw_aquarium_fish
from pesca_conquistas import commit_with_achievements
from pesca_aquario_decor import selections
from pesca_aquario_decor_visual import aquarium_background
import copy


class AquariumView(QWidget):
    WIDTH, HEIGHT = 256, 128

    def __init__(self, state_getter, catalogue, parent=None):
        super().__init__(parent)
        self.state_getter = state_getter
        self.catalogue = catalogue
        self.phase = 0.0
        self.clock = QElapsedTimer()
        self.timer = QTimer(self)
        self.timer.setInterval(66)
        self.timer.timeout.connect(self.advance_frame)
        QApplication.instance().applicationStateChanged.connect(self.application_state)
        self.setMinimumSize(256, 128)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setAccessibleName('Aquário de descobertas, até três espécies')
        self.background = self.make_background()
        self.decoration_preview = {}

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        ratio = self.devicePixelRatioF()
        scale = max(1, int(width*ratio/self.WIDTH))
        return max(128, math.ceil(self.HEIGHT*scale/ratio))

    def showEvent(self, event):
        super().showEvent(event)
        self.clock.start()
        self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def application_state(self, state):
        if state == Qt.ApplicationActive and self.isVisible():
            self.clock.start()
            self.timer.start()
        else:
            self.timer.stop()

    def advance_frame(self):
        self.phase += min(.25, self.clock.restart()/1000)
        self.update()

    @staticmethod
    def make_background():
        return aquarium_background()

    def fish_positions(self, phase):
        state = self.state_getter()
        result = []
        for slot, id_ in enumerate(state['museu']['aquario']):
            if slot_status(state, slot, self.catalogue) == 'exibida':
                angle = phase*.19+slot*2.2
                scale=scale_for(exhibit(state,slot),id_)
                width,height=36*scale,24*scale
                amplitude=112-width/2-2
                bob=max(0,min(2,(30-height)/2-1))
                result.append((id_, 128+amplitude*math.sin(angle),
                               31+slot*30+bob*math.sin(phase*.7+slot), math.cos(angle)<0))
        return result

    def render_image(self, phase=None, detail=1):
        phase = self.phase if phase is None else phase
        if detail not in (1, 2):
            raise ValueError('Aquarium detail must be 1 or 2.')
        state=self.state_getter()
        selection=selections(state,self.decoration_preview)
        background=aquarium_background(selection) if any(selection) else self.background
        image = background.scaled(256*detail,128*detail,
                                      Qt.IgnoreAspectRatio,Qt.FastTransformation)
        p = QPainter(image)
        p.scale(detail,detail)
        p.setClipRect(16,16,224,90)
        for i in range(7):
            x = 24+(i*31)%205
            y = 100-int((phase*7+i*17)%80)
            p.setPen(QColor('#76b2b3'));p.drawRect(x,y,2,3)
            p.fillRect(x+1,y,1,1,QColor('#c0dfd0'))
        for id_, x, y, reverse in self.fish_positions(phase):
            slot=state['museu']['aquario'].index(id_)
            draw_aquarium_fish(p,id_,x,y,exhibit(state,slot),reverse,detail,phase)
        p.setPen(QColor('#7eafb1'))
        for i in range(4):
            x = 22+i*55+int(3*math.sin(phase*.4+i))
            p.drawLine(x,19,x+22,19)
        p.end()
        return image

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(),QColor('#1c2b3b'))
        ratio = self.devicePixelRatioF()
        scale = max(1, int(min(self.width()*ratio/256,self.height()*ratio/128)))
        width, height = 256*scale/ratio,128*scale/ratio
        target = QRectF(round((self.width()-width)*ratio/2)/ratio,
                        round((self.height()-height)*ratio/2)/ratio,width,height)
        painter.setRenderHint(QPainter.SmoothPixmapTransform,False)
        painter.drawImage(target,self.render_image(detail=2 if scale>=2 else 1))
        painter.end()


class MuseuDialog(QDialog):
    def __init__(self, game, catalogue=None):
        super().__init__(game)
        self.game = game
        self.catalogue = ESPECIES if catalogue is None else catalogue
        self._signature = None
        self.setWindowTitle('Museu — Aquário de descobertas')
        self.setWindowFlag(Qt.WindowStaysOnTopHint,not mobile())
        geo = QApplication.primaryScreen().availableGeometry()
        self.resize(geo.width() if mobile() else min(640,geo.width()-20),
                    geo.height() if mobile() else min(700,geo.height()-20))
        self.setMinimumSize(280,180)
        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(8,8,8,8)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.outer.addWidget(self.scroll)
        content = QWidget()
        content.setObjectName('museuConteudo')
        content.setStyleSheet('#museuConteudo { background: #1c2b3b; }')
        self.body = QVBoxLayout(content)
        self.body.setContentsMargins(12,12,12,12)
        self.body.setSpacing(8)
        self.scroll.setWidget(content)
        QScroller.grabGesture(self.scroll.viewport(),QScroller.TouchGesture)
        heading = self.label('Museu das Oito Águas')
        heading.setProperty('heading',True)
        self.body.addWidget(heading)
        self.body.addWidget(self.label('Aquário de descobertas\nExiba até três espécies diferentes. Descobrir libera a representação: nenhuma captura ou moeda é consumida.'))
        decorate=QPushButton('Decorar aquário')
        decorate.clicked.connect(self.open_decorations)
        self.body.addWidget(decorate)
        self.aquario = AquariumView(lambda:self.game.estado,self.catalogue,self)
        self.body.addWidget(self.aquario)
        self.status = self.label('')
        self.body.addWidget(self.status)
        self.selectors, self.remove_buttons, self.details = [], [], []
        self.specimen_selectors=[]
        for slot in range(CAPACIDADE):
            self.body.addWidget(self.label(f'Espaço {slot+1}'))
            row = QHBoxLayout()
            combo = QComboBox()
            combo.setAccessibleName(f'Espécie no espaço {slot+1}')
            combo.setMinimumContentsLength(8)
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumWidth(0)
            combo.setIconSize(QSize(36,24))
            remove = QPushButton('Retirar')
            remove.setAccessibleName(f'Retirar espécie do espaço {slot+1}')
            combo.currentIndexChanged.connect(lambda _,i=slot:self.choose(i))
            remove.clicked.connect(lambda _,i=slot:self.apply(i,None))
            row.addWidget(combo,1);row.addWidget(remove)
            self.body.addLayout(row)
            detail = self.label('')
            self.body.addWidget(detail)
            specimen=QComboBox()
            specimen.setAccessibleName(f'Exemplar no espaço {slot+1}')
            specimen.addItem('Maior exemplar conhecido','maior')
            specimen.addItem('Menor exemplar conhecido','menor')
            specimen.currentIndexChanged.connect(lambda _,i=slot:self.choose_specimen(i))
            self.body.addWidget(specimen)
            self.specimen_selectors.append(specimen)
            self.selectors.append(combo);self.remove_buttons.append(remove);self.details.append(detail)
        self.feedback = self.label('')
        self.feedback.setStyleSheet('color: #ffe3ac')
        self.body.addWidget(self.feedback)
        self.body.addWidget(self.label('Comprimentos de design provisórios. Escala visual comprimida por espécie, não uma comparação real entre espécies. Sem medida: representação padrão. Sem alimentação, renda ou perda por ausência.'))
        self.back = QPushButton('Voltar à pescaria')
        self.back.clicked.connect(self.accept)
        self.body.addWidget(self.back)
        self.aquario.timer.timeout.connect(self.refresh)
        self.finished.connect(self.aquario.timer.stop)
        self.refresh()

    @staticmethod
    def label(text):
        label = QLabel(text)
        label.setTextFormat(Qt.PlainText)
        label.setWordWrap(True)
        label.setMinimumWidth(0)
        label.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
        return label

    def showEvent(self,event):
        super().showEvent(event)
        QTimer.singleShot(0,self.insets)

    def insets(self,*_):
        handle = self.windowHandle()
        if mobile() and handle is not None:
            m = handle.safeAreaMargins()
            self.outer.setContentsMargins(m.left()+4,m.top()+4,m.right()+4,m.bottom()+4)
            if not getattr(self,'_safe_connected',False):
                handle.safeAreaMarginsChanged.connect(self.insets)
                self._safe_connected = True

    def refresh(self):
        state = self.game.estado
        slots = state['museu']['aquario']
        signature = (tuple(state['inventario_por_id'].items()),tuple(slots),
                     repr(state.get('medidas_peixes',{})),tuple(state['museu'].get('exemplares',['maior']*3)))
        if signature == self._signature:
            return
        self._signature = signature
        available = eligible_species(state,self.catalogue)
        shown = sum(slot_status(state,i,self.catalogue)=='exibida' for i in range(CAPACIDADE))
        if not available:
            self.status.setText('Aquário vazio. Descubra um peixe para começar. Encontros especiais não são elegíveis.')
        else:
            self.status.setText(f'{shown}/3 espécies em exposição · {len(available)} descobertas elegíveis'+
                                ('\nEscolha abaixo seu primeiro morador.' if not shown else ''))
        for slot, combo in enumerate(self.selectors):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(f'Espaço {slot+1} · vazio',None)
            for id_ in available:
                combo.addItem(QIcon(QPixmap.fromImage(species_image(id_))),self.catalogue[id_]['nome'],id_)
                if id_ in slots and id_ != slots[slot]:
                    combo.model().item(combo.count()-1).setEnabled(False)
            current = slots[slot]
            status = slot_status(state,slot,self.catalogue)
            if current is not None and current not in available:
                combo.addItem('Referência preservada: '+current[:60],current)
                combo.model().item(combo.count()-1).setEnabled(False)
            combo.setCurrentIndex(max(0,combo.findData(current)))
            combo.blockSignals(False)
            combo.setEnabled(bool(available))
            self.remove_buttons[slot].setEnabled(current is not None)
            if status == 'vazio':
                text = f'Espaço {slot+1} disponível.'
            elif status == 'exibida':
                s = self.catalogue[current]
                count = state['inventario_por_id'][current]
                text = f"{s['nome']} · {count} {'registro' if count == 1 else 'registros'}\n{s['cientifico']}"
                measured=exhibit(state,slot)
                choice=state['museu'].get('exemplares',['maior']*3)[slot]
                text+='\n'+('Em exposição: '+choice+' exemplar · '+fmt_length(measured['mm']) if measured else 'Sem exemplar medido · representação padrão')
            else:
                text = 'Seleção indisponível: '+current[:72]+'. Referência guardada; troque ou retire para liberar este espaço.'
            self.details[slot].setText(text)
            specimen=self.specimen_selectors[slot]
            specimen.blockSignals(True)
            record=state.get('medidas_peixes',{}).get('records',{}).get(current)
            for index,kind in enumerate(('maior','menor')):
                length=fmt_length(record[kind]['mm']) if record else 'sem medida'
                specimen.setItemText(index,kind.title()+' exemplar · '+length)
            specimen.setCurrentIndex(0 if state['museu'].get('exemplares',['maior']*3)[slot]=='maior' else 1)
            specimen.setEnabled(status=='exibida' and exhibit(state,slot) is not None)
            specimen.blockSignals(False)
        self.aquario.update()

    def choose(self,slot):
        self.apply(slot,self.selectors[slot].currentData())

    def open_decorations(self):
        from pesca_aquario_decor_ui import DecorationDialog
        dialog=DecorationDialog(self.game,self)
        dialog.exec();dialog.deleteLater()
        self.aquario.update()

    def choose_specimen(self,slot):
        choice=self.specimen_selectors[slot].currentData()
        if choice not in ('menor','maior') or exhibit(self.game.estado,slot) is None:
            return
        candidate=copy.deepcopy(self.game.estado)
        candidate['museu'].setdefault('exemplares',['maior']*3)[slot]=choice
        failed=not commit_with_achievements(self.game,candidate)
        if failed:
            self.feedback.setText('Exemplar não salvo. Seleção anterior mantida. '+str(self.game._save_error))
        else:
            measured=exhibit(self.game.estado,slot)
            self.feedback.setText(f'Espaço {slot+1}: {choice} exemplar · '+fmt_length(measured['mm'])+'. Seleção salva.')
        self._signature=None;self.refresh()
        if failed:
            QTimer.singleShot(0,self,lambda:self.scroll.ensureWidgetVisible(self.feedback,0,12))

    def apply(self,slot,species_id):
        failed = False
        try:
            candidate = change_exhibit(self.game.estado,slot,species_id,self.catalogue)
            if candidate == self.game.estado:
                return
            if not commit_with_achievements(self.game,candidate):
                failed = True
                self.feedback.setText('Exposição não salva. '+str(self.game._save_error))
            else:
                self.feedback.setText('Exposição salva. Capturas e moedas preservadas.')
        except ValueError as exc:
            failed = True
            self.feedback.setText(str(exc))
        self._signature = None
        self.refresh()
        if failed:
            # Wait for the wrapped label/layout, then reveal errors on short
            # screens. The QObject context cancels this callback on deletion.
            QTimer.singleShot(0,self,lambda:self.scroll.ensureWidgetVisible(self.feedback,0,12))
