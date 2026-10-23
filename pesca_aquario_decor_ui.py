"""Store/editor shared by the aquarium, with disposable previews and atomic commits."""
from PySide6.QtCore import Qt, QSize, Signal, QEvent
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QWidget,QDialog,QVBoxLayout,QHBoxLayout,QBoxLayout,
    QLabel,QComboBox,QListWidget,QListWidgetItem,QPushButton,QSizePolicy,QLayout)
from pesca_aquario_decor import (CAT,CATALOGO,SLOTS,record,purchase,equip,restore_default)
from pesca_aquario_decor_visual import aquarium_background
from pesca_museu_ui import AquariumView
from pesca_catalogo import ESPECIES

def money_cent(value):
    whole,fraction=divmod(value,100)
    return f'{whole:,}'.replace(',','.')+((','+f'{fraction:02d}'.rstrip('0')) if fraction else '')

def label(text=''):
    result=QLabel(text);result.setTextFormat(Qt.PlainText);result.setWordWrap(True);result.setMinimumWidth(0)
    result.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
    return result

class DecorationPanel(QWidget):
    changed=Signal()
    def __init__(self,game,shop=False,parent=None):
        super().__init__(parent);self.game=game;self.shop=shop;self.signature=None;self.preview_requested=True
        self.setObjectName('aquarioDecorConteudo')
        self.setStyleSheet('#aquarioDecorConteudo { background: #1c2b3b; }')
        self.setAttribute(Qt.WA_StyledBackground,True)
        self.setMinimumWidth(0)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        layout.addWidget(label('Decorações permanentes e apenas visuais. Trocar ou retirar é gratuito.'))
        filters=QHBoxLayout();self.area=QComboBox();self.slot=QComboBox()
        self.area.setAccessibleName('Área da decoração');self.slot.setAccessibleName('Tipo de decoração')
        for combo in (self.area,self.slot):
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(4);combo.setMinimumWidth(0)
        for name,value in [('Todas as áreas',None),('Internas','interna'),('Externas','externa')]:self.area.addItem(name,value)
        self.slot.addItem('Todos os tipos',None)
        for key,value in SLOTS.items():self.slot.addItem(value['nome'],key)
        filters.addWidget(self.area,1);filters.addWidget(self.slot,1);layout.addLayout(filters)
        self.body=QBoxLayout(QBoxLayout.LeftToRight)
        left=QVBoxLayout();self.list=QListWidget();self.list.setAccessibleName('Decorações do aquário')
        self.list.setIconSize(QSize(72,36));self.list.setWordWrap(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.list.setMinimumHeight(160)
        left.addWidget(self.list,1)
        self.details=label();left.addWidget(self.details)
        self.action=QPushButton();self.action.clicked.connect(self.apply);left.addWidget(self.action)
        self.clear=QPushButton('Usar visual original nesta categoria');self.clear.clicked.connect(self.clear_slot);left.addWidget(self.clear)
        self.body.addLayout(left,1)
        right=QVBoxLayout();self.preview_title=label('Prévia do aquário · só é salva ao colocar/comprar')
        right.addWidget(self.preview_title)
        self.aquarium=AquariumView(lambda:self.game.estado,ESPECIES,self)
        right.addWidget(self.aquarium);right.addWidget(label('Escolha até uma decoração de cada tipo. As decorações ficam atrás dos peixes.'))
        reset=QPushButton('Restaurar todo o visual original');reset.clicked.connect(self.restore)
        right.addWidget(reset);right.addStretch(1);self.body.addLayout(right,1);layout.addLayout(self.body,1)
        self.feedback=label();self.feedback.setStyleSheet('color: #ffe3ac');layout.addWidget(self.feedback)
        self.area.currentIndexChanged.connect(self.filter_changed);self.slot.currentIndexChanged.connect(self.filter_changed)
        self.list.currentItemChanged.connect(self.select);self.refresh()
        self.window().installEventFilter(self)

    def eventFilter(self,obj,event):
        if event.type()==QEvent.Resize and obj is self.window():
            self.body.setDirection(QBoxLayout.TopToBottom if obj.width()<650 else QBoxLayout.LeftToRight)
        return super().eventFilter(obj,event)

    def resizeEvent(self,event):
        self.body.setDirection(QBoxLayout.TopToBottom if self.window().width()<650 else QBoxLayout.LeftToRight)
        super().resizeEvent(event)

    def current_id(self):
        item=self.list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def filter_changed(self,*_):
        self.signature=None;self.refresh()

    def refresh(self):
        state=self.game.estado;decor=record(state);current=self.current_id()
        signature=(tuple(decor['compradas']),tuple(decor['equipadas'].items()),self.area.currentData(),self.slot.currentData())
        if signature!=self.signature:
            self.signature=signature;self.list.blockSignals(True);self.list.clear()
            for item in CATALOGO:
                if not self.shop and item['id'] not in decor['compradas']:continue
                if self.area.currentData() and item['area']!=self.area.currentData():continue
                if self.slot.currentData() and item['slot']!=self.slot.currentData():continue
                status=('em uso' if decor['equipadas'][item['slot']]==item['id'] else 'adquirida'
                        if item['id'] in decor['compradas'] else money_cent(item['price']*100)+' moedas')
                row=QListWidgetItem(item['nome']+'\n'+SLOTS[item['slot']]['nome']+' · '+status)
                selection=tuple(item['id'] if key==item['slot'] else None for key in SLOTS)
                row.setIcon(QIcon(QPixmap.fromImage(aquarium_background(selection))))
                row.setSizeHint(QSize(0,64));row.setData(Qt.UserRole,item['id']);self.list.addItem(row)
            index=next((i for i in range(self.list.count()) if self.list.item(i).data(Qt.UserRole)==current),0)
            self.list.setCurrentRow(index);self.list.blockSignals(False)
        self.update_selection()

    def select(self,*_):
        self.preview_requested=True;self.update_selection()

    def update_selection(self):
        id_=self.current_id();decor=record(self.game.estado)
        self.aquarium.decoration_preview={}
        if not id_:
            self.details.setText('Nenhuma decoração neste filtro.' if self.shop else 'Nenhuma decoração adquirida neste filtro. Compre decorações na loja para começar.')
            self.action.setEnabled(False);self.action.setText('Selecione uma decoração');self.clear.setEnabled(False)
        else:
            item=CAT[id_]
            if self.preview_requested:self.aquarium.decoration_preview={item['slot']:id_}
            self.details.setText(item['description']+'\n'+('Interna' if item['area']=='interna' else 'Externa')+' · '+SLOTS[item['slot']]['nome'])
            owned=id_ in decor['compradas'];active=decor['equipadas'][item['slot']]==id_
            self.action.setText('Em uso' if active else 'Colocar no aquário' if owned else 'Comprar e colocar ('+money_cent(item['price']*100)+' moedas)')
            self.action.setEnabled(not active and (owned or (self.shop and self.game.estado.get('moedas_centavos',0)>=item['price']*100)))
            self.clear.setEnabled(decor['equipadas'][item['slot']] is not None)
        self.preview_title.setText('Prévia do aquário · só é salva ao colocar/comprar' if self.preview_requested and id_ else 'Seu aquário · visual atual')
        self.aquarium.update()

    def commit(self,candidate,message):
        if not self.game._commit(candidate):
            self.feedback.setText('Alteração não salva. '+str(getattr(self.game,'_save_error','')))
            self.signature=None;self.refresh();return
        self.feedback.setText(message);self.preview_requested=False;self.signature=None;self.refresh();self.changed.emit()
        tooltip=getattr(self.game,'atualizar_tooltip',None)
        if tooltip:tooltip()
        self.game.update()

    def apply(self):
        id_=self.current_id()
        if not id_:return
        if hasattr(self.game,'tick'):self.game.tick()
        if getattr(self.game,'_save_error',None):
            self.feedback.setText('Não foi possível salvar. '+str(self.game._save_error));return
        try:
            if id_ in record(self.game.estado)['compradas']:
                candidate=equip(self.game.estado,CAT[id_]['slot'],id_);message='Decoração colocada. Troca gratuita.'
            elif self.shop:
                candidate=purchase(self.game.estado,id_);message='Decoração comprada e colocada no aquário.'
            else:raise ValueError('Compre esta decoração na loja.')
            self.commit(candidate,message)
        except ValueError as exc:self.feedback.setText(str(exc));self.refresh()

    def clear_slot(self):
        id_=self.current_id()
        if id_:self.commit(equip(self.game.estado,CAT[id_]['slot'],None),'Visual original nesta categoria. A compra foi mantida.')

    def restore(self):
        self.commit(restore_default(self.game.estado),'Visual original restaurado. Todas as compras foram mantidas.')

class DecorationDialog(QDialog):
    def __init__(self,game,parent=None):
        super().__init__(parent or game);self.game=game
        self.setWindowTitle('Decorar aquário');self.resize(740,640);self.setMinimumSize(280,220)
        layout=QVBoxLayout(self);heading=label('Seu aquário, do seu jeito');heading.setProperty('heading',True);layout.addWidget(heading)
        from PySide6.QtWidgets import QScrollArea
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.panel=DecorationPanel(game,parent=self);scroll.setWidget(self.panel);layout.addWidget(scroll)
        buttons=QVBoxLayout()
        if hasattr(game,'abrir_loja'):
            shop=QPushButton('Comprar decorações na loja');shop.clicked.connect(self.open_shop);buttons.addWidget(shop)
        close=QPushButton('Voltar ao museu');close.clicked.connect(self.accept);buttons.addWidget(close);layout.addLayout(buttons)
        self.finished.connect(self.panel.aquarium.timer.stop)

    def open_shop(self):
        self.accept();self.game.abrir_loja(decoracoes=True)
