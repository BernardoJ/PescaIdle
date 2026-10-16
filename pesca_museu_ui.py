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
        image = QImage(256, 128, QImage.Format_ARGB32_Premultiplied)
        image.fill(QColor('#263749'))
        p = QPainter(image)
        def box(x, y, w, h, color):
            p.fillRect(x, y, w, h, QColor(color))
        for y in range(0, 128, 16):
            box(0, y, 256, 1, '#32465a')
            for x in range((y//16 % 2)*16, 256, 32):
                box(x, y, 1, 16, '#32465a')
        box(7, 8, 242, 108, '#101e2b')
        for inset, color in ((0,'#ba9860'),(1,'#f0d39b'),(3,'#69513c'),(5,'#a9c8bf')):
            p.setPen(QColor(color));p.drawRect(8+inset,9+inset,239-2*inset,104-2*inset)
        for y in range(16, 106):
            depth = (y-16)/90
            box(15,y,226,1,QColor(int(29-depth*13),int(91-depth*47),int(108-depth*48)).name())
        p.setPen(Qt.NoPen)
        for x in (42, 114, 191):
            p.setBrush(QColor(162,217,199,16))
            p.drawPolygon(QPolygon([QPoint(x,16),QPoint(x+8,16),QPoint(x+33,105),QPoint(x-14,105)]))
            box(x-6,5,22,4,'#d2af76');box(x-2,10,14,2,'#f5dca0')
        box(15,102,226,6,'#aa9d78')
        for i in range(38):
            box(17+i*6,103+i%3,2,1,'#6d7b70')
        for x, height in ((27,28),(37,18),(220,33),(230,22)):
            for y in range(height):
                box(x+round(2*math.sin(y*.4)),103-y,2,2,'#507e70')
                if y%6 == 0:
                    box(x-3,103-y,5,2,'#729e7a')
        for x, width in ((43,18),(185,23)):
            box(x,99,width,5,'#566d70');box(x+3,95,width-6,5,'#77948c')
            box(x+5,95,width-9,1,'#9bb0a0')
        box(8,115,240,4,'#ab8753');box(12,119,232,9,'#514333')
        for x in (20, 76, 132, 188):
            box(x,120,47,2,'#776042')
        p.end()
        return image

    def fish_positions(self, phase):
        state = self.state_getter()
        result = []
        for slot, id_ in enumerate(state['museu']['aquario']):
            if slot_status(state, slot, self.catalogue) == 'exibida':
                angle = phase*.19+slot*2.2
                result.append((id_, round(128+78*math.sin(angle)),
                               34+slot*23+round(3*math.sin(phase*.7+slot)), math.cos(angle)<0))
        return result

    def render_image(self, phase=None):
        phase = self.phase if phase is None else phase
        image = self.background.copy()
        p = QPainter(image)
        p.setClipRect(16,16,224,90)
        for i in range(7):
            x = 24+(i*31)%205
            y = 100-int((phase*7+i*17)%80)
            p.setPen(QColor('#76b2b3'));p.drawRect(x,y,2,3)
            p.fillRect(x+1,y,1,1,QColor('#c0dfd0'))
        for id_, x, y, reverse in self.fish_positions(phase):
            sprite = species_image(id_)
            if reverse:
                sprite = sprite.mirrored(True,False)
            p.drawImage(x-18,y-12,sprite)
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
        painter.drawImage(target,self.render_image())
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
        self.aquario = AquariumView(lambda:self.game.estado,self.catalogue,self)
        self.body.addWidget(self.aquario)
        self.status = self.label('')
        self.body.addWidget(self.status)
        self.selectors, self.remove_buttons, self.details = [], [], []
        for slot in range(CAPACIDADE):
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
            self.selectors.append(combo);self.remove_buttons.append(remove);self.details.append(detail)
        self.feedback = self.label('')
        self.feedback.setStyleSheet('color: #ffe3ac')
        self.body.addWidget(self.feedback)
        self.body.addWidget(self.label('Ilustrações da coleção, sem simular habitat ou escala real. Informações completas ficam na Enciclopédia. Sem alimentação, renda ou perda por ausência.'))
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
        signature = (tuple(state['inventario_por_id'].items()),tuple(slots))
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
            else:
                text = 'Seleção indisponível: '+current[:72]+'. Referência guardada; troque ou retire para liberar este espaço.'
            self.details[slot].setText(text)
        self.aquario.update()

    def choose(self,slot):
        self.apply(slot,self.selectors[slot].currentData())

    def apply(self,slot,species_id):
        failed = False
        try:
            candidate = change_exhibit(self.game.estado,slot,species_id,self.catalogue)
            if candidate == self.game.estado:
                return
            if not self.game._commit(candidate):
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
