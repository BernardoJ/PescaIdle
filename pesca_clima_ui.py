"""Daily-weather consultation; selection controls never change the calendar."""
from PySide6.QtCore import Qt,QTimer,QSize
from PySide6.QtGui import QIcon,QPixmap,QColor
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QListWidget,QListWidgetItem,QPushButton,QScrollArea
from pesca_clima import CLIMAS,IDS,DATA,affinities,factor,context
from pesca_catalogo import ESPECIES,LOCAIS,eligible
from pesca_tempo import snapshot
from pesca_clima_visual import weather_image
from pesca_especies_visual import species_image
from pesca_plataforma import mobile
from datetime import timezone,timedelta


def weather_clock(game):
    moment=getattr(game,'_preview_clock',None)
    if moment is None:return getattr(game,'_clock_snapshot',None) or snapshot(game._wall() if hasattr(game,'_wall') else None)
    offset=game.estado.get('contexto_fuso',snapshot()['offset_seconds'])
    if moment.utcoffset() is None:moment=moment.replace(tzinfo=timezone(timedelta(seconds=offset)))
    return snapshot(moment.timestamp(),int(moment.utcoffset().total_seconds()))


def current_weather(game):
    clock=weather_clock(game)
    result=context(game.estado,clock['utc'],clock['offset_seconds'])
    preview=getattr(game,'_preview_weather',None)
    if preview in IDS:result={**result,'id':preview,'rotulo':CLIMAS[preview]['name']}
    return result


class ClimateDialog(QDialog):
    def fit_mobile(self):
        from PySide6.QtWidgets import QApplication,QComboBox
        self.setWindowFlag(Qt.WindowStaysOnTopHint,False);self.setMinimumSize(0,0)
        self.icon.setFixedSize(40,40)
        for combo in self.findChildren(QComboBox):
            combo.setMinimumContentsLength(12);combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        def insets(*_):
            handle=self.windowHandle()
            if handle is not None:
                m=handle.safeAreaMargins();self.layout().setContentsMargins(m.left()+14,m.top()+14,m.right()+14,m.bottom()+14)
                if not getattr(self,'_climate_safe_connected',False):
                    handle.safeAreaMarginsChanged.connect(insets);self._climate_safe_connected=True
        QTimer.singleShot(0,insets)
        self.resize(QApplication.primaryScreen().availableGeometry().size())
        return self

    def __init__(self,game):
        super().__init__(game);self.game=game;self.setWindowTitle('Clima de hoje')
        self.setWindowFlag(Qt.WindowStaysOnTopHint,True);self.resize(650,590)
        layout=QVBoxLayout(self);layout.setContentsMargins(14,14,14,14);layout.setSpacing(6)
        head=QHBoxLayout();self.icon=QLabel();self.heading=QLabel();self.heading.setProperty('heading',True)
        self.icon.setFixedSize(40,40)
        head.addWidget(self.icon);head.addWidget(self.heading,1);layout.addLayout(head)
        self.summary=QLabel();self.summary.setWordWrap(True);layout.addWidget(self.summary)
        self.map=QComboBox();self.map.setAccessibleName('Filtrar afinidades por mapa');self.map.addItem('Todos os mapas',None)
        for mid,row in LOCAIS.items():self.map.addItem(row['nome'],mid)
        layout.addWidget(self.map)
        legend=QLabel('Pesos de encontro; chances normalizadas.\n† Adaptação indireta. Respeita local e horário.')
        legend.setStyleSheet('font-size: 13px;')
        legend.setWordWrap(True);layout.addWidget(legend)
        self.list=QListWidget();self.list.setIconSize(QSize(42,28));self.list.setAccessibleName('Espécies com bônus e ônus')
        self.list.setWordWrap(True);self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.list,1)
        self.detail=QLabel('Selecione uma espécie para consultar o motivo da afinidade.');self.detail.setWordWrap(True)
        self.detail.setStyleSheet('font-size: 13px; color: #c6d4cd; background: #1b2b3c; padding: 5px;')
        self.detail.setTextFormat(Qt.PlainText);self.detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.detail_scroll=QScrollArea();self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.detail_scroll.setWidget(self.detail)
        self.detail_scroll.setStyleSheet('QScrollArea { background: #1b2b3c; border: 1px solid #586d78; }')
        self.detail_scroll.viewport().setStyleSheet('background: #1b2b3c;')
        self.detail_scroll.setFixedHeight(64 if mobile() else 86);layout.addWidget(self.detail_scroll)
        button=QPushButton('Voltar à pescaria');button.clicked.connect(self.accept);layout.addWidget(button)
        self.map.currentIndexChanged.connect(self.refresh);self.list.currentItemChanged.connect(self.show_detail)
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(750)
        self.finished.connect(self.timer.stop);self._signature=None;self.refresh()

    def showEvent(self,event):
        # Generic mobile fitting changes QLabel minimum widths; restore the
        # fixed icon after fitting so it cannot collapse beside the title.
        self.icon.setFixedSize(40,40)
        super().showEvent(event)

    def poll(self):
        weather=current_weather(self.game);period=weather_clock(self.game)['periodo_id']
        signature=weather['id'],weather['data'],period
        if signature!=self._signature:self.refresh()

    def refresh(self,*_):
        weather=current_weather(self.game);period=weather_clock(self.game)['periodo_id']
        self._signature=weather['id'],weather['data'],period
        self.icon.setPixmap(QPixmap.fromImage(weather_image(weather['id'] if weather['id'] in IDS else 'ameno')).scaled(40,40,Qt.KeepAspectRatio,Qt.FastTransformation))
        self.heading.setText(weather['rotulo'])
        self.summary.setText('Mesmo clima nos oito mapas até 00:00.\n'+weather['data'])
        selected=self.list.currentItem();selected=selected.data(Qt.UserRole) if selected else None
        scroll=self.list.verticalScrollBar().value();self.list.clear()
        rows=affinities(weather['id'],self.map.currentData(),period)
        rows.sort(key=lambda r:(0 if r['percent']>0 else 1,LOCAIS[r['map_id']]['nome'],ESPECIES[r['species_id']]['nome']))
        for row in rows:
            name=ESPECIES[row['species_id']]['nome'];mark=' †' if row['experimental'] else ''
            available=row['species_id'] in {o['species_id'] for o in eligible(row['map_id'],period)}
            status='Ativo no horário atual' if row['active'] and available else 'Fora do horário da espécie' if row['active'] else 'Neutro à noite; efeito com luz ou crepúsculo'
            item=QListWidgetItem(f"{name} {row['percent']:+d}%{mark}\n{LOCAIS[row['map_id']]['nome']} · {status}")
            item.setData(Qt.UserRole,row);item.setForeground(QColor('#b8e6c3' if row['percent']>0 else '#f0b9a0'))
            item.setIcon(QIcon(QPixmap.fromImage(species_image(row['species_id']))));item.setToolTip(row['reason'])
            self.list.addItem(item)
            if selected and selected['species_id']==row['species_id'] and selected['map_id']==row['map_id']:self.list.setCurrentItem(item)
        if not rows:
            self.list.addItem('Pesos neutros neste clima/local. Todas as afinidades têm fator 1,00.')
            self.detail.setText('Ameno conserva as regras habituais de encontro.' if weather['id']=='ameno' else 'Nenhum modificador climático específico para este local.')
        elif self.list.currentRow()<0:self.list.setCurrentRow(0)
        self.list.verticalScrollBar().setValue(scroll)

    def show_detail(self,*_):
        item=self.list.currentItem();row=item.data(Qt.UserRole) if item else None
        if not row:return
        sources='; '.join(DATA['sources'][sid]['title'] for sid in row['sources'])
        self.detail.setText(row['reason']+'\nBase: '+sources)
