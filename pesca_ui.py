"""Readable desktop UI, with stepped pixel borders and warm brass accents."""
from PySide6.QtCore import Qt, QRect
import os
from pathlib import Path
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter, QPen, QIcon, QImage, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton
from pesca_visual import resource_path


def configure_app(app):
    # Qt's offscreen plugin does not discover Windows fonts. Register system
    # faces explicitly so source, frozen builds and QA have identical metrics.
    fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    for name in ('segoeui.ttf', 'segoeuib.ttf', 'seguisym.ttf'):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))
    app.setStyle('Fusion')
    frame=str(resource_path('painel.png')).replace('\\','/')
    app.setStyleSheet(STYLE + f'''
QDialog, QMessageBox {{ border-image: url("{frame}") 8 8 8 8 stretch stretch; border-width: 8px; }}
QMenu {{ border-image: url("{frame}") 8 8 8 8 stretch stretch; border-width: 8px; padding: 6px; }}
QMenu::icon {{ margin-left: 8px; }}
QListWidget {{ border-image: url("{frame}") 8 8 8 8 stretch stretch; border-width: 8px; }}
QLabel[panel="true"] {{ border-image: url("{frame}") 8 8 8 8 stretch stretch; border-width: 8px; }}
''')


_ICONS = {}
_ITEM_ICONS = {}


def cosmetic_icon(renderer, slot, id_):
    key=(slot,id_)
    if key not in _ITEM_ICONS:
        sprite=renderer.item_image(slot,id_)
        tile=QImage(32,32,QImage.Format_ARGB32_Premultiplied)
        tile.fill(Qt.transparent)
        p=QPainter(tile)
        if id_.endswith('_nenhum'):
            p.setPen(QPen(QColor('#a4b9b4'),2))
            p.drawRect(9,9,14,14)
            p.drawLine(7,25,25,7)
        else:
            if sprite.width()>30 or sprite.height()>30:
                sprite=sprite.scaled(30,30,Qt.KeepAspectRatio,Qt.FastTransformation)
            p.drawImage((32-sprite.width())//2,(32-sprite.height())//2,sprite)
        p.end()
        _ITEM_ICONS[key]=QIcon(QPixmap.fromImage(tile))
    return _ITEM_ICONS[key]


def rpg_icon(name):
    if name not in _ICONS:
        _ICONS[name] = QIcon(str(resource_path('icone-'+name+'.png')))
    return _ICONS[name]


class InfoDialog(QDialog):
    """The same RPG panel for offline progress, status and achievements.

    A scrollable page keeps even a complete inventory inside the available screen.
    """
    def __init__(self,game,title,text):
        super().__init__(game)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowStaysOnTopHint,True)
        geo=QApplication.primaryScreen().availableGeometry()
        self.resize(min(510,geo.width()-20),min(440,geo.height()-20))
        self.setMinimumSize(min(330,geo.width()-20),min(240,geo.height()-20))
        layout=QVBoxLayout(self);layout.setContentsMargins(20,18,20,18)
        heading=QHBoxLayout();icon=QLabel()
        icon.setPixmap(rpg_icon('conquistas' if title=='Conquistas' else 'livro').pixmap(32,32))
        heading.addWidget(icon)
        label=QLabel(title);label.setProperty('heading',True);heading.addWidget(label,1)
        layout.addLayout(heading)
        self.page=QLabel(text);self.page.setTextFormat(Qt.PlainText)
        self.page.setWordWrap(True);self.page.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        self.page.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.page.setProperty('panel',True)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.NoFrame);self.scroll.setWidget(self.page)
        layout.addWidget(self.scroll,1)
        button=QPushButton('Voltar à pescaria');button.setDefault(True)
        button.clicked.connect(self.accept);layout.addWidget(button)
        x=max(geo.x()+8,game.x()-self.width()-10)
        y=max(geo.y()+8,min(game.y(),geo.bottom()-self.height()-8))
        self.move(x,y)

STYLE = """
QWidget { color: #f4e7ca; font-family: 'Segoe UI'; font-size: 10pt; }
QDialog, QMessageBox { background: #253647; }
QLabel { background: transparent; }
QLabel[heading="true"] { color: #efc581; font-size: 17pt; font-weight: 600; }
QLabel[panel="true"] { background: #1c2b3b; border: 1px solid #697d80; padding: 14px; }
QTabWidget::pane { background: #1c2b3b; border: 2px solid #8e8a70; top: -1px; }
QTabBar::tab { background: #2f4351; color: #c6d1c6; padding: 8px 9px; border: 1px solid #697d80; }
QTabBar::tab:selected { background: #506b6a; color: #ffe3ac; border-bottom: 2px solid #e6b96b; }
QTabBar::tab:hover { background: #40595e; }
QListWidget, QComboBox { background: #1b2b3c; border: 1px solid #697d80; padding: 5px; selection-background-color: #486967; }
QListWidget::item { padding: 8px 5px; border-bottom: 1px solid #304651; }
QListWidget::item:selected { color: #fff1cf; background: #486967; border-left: 3px solid #e6b96b; }
QListWidget::item:hover { background: #354d58; }
QComboBox { min-height: 24px; }
QComboBox QAbstractItemView { background: #253647; selection-background-color: #486967; }
QPushButton { background: #38535b; color: #ffe3ac; border: 2px solid #b69a68; padding: 8px 14px; min-height: 20px; }
QPushButton:hover { background: #506c69; border-color: #f3d39a; }
QPushButton:pressed { background: #223e4c; border-color: #d8b277; }
QPushButton:focus { border-color: #fff0bf; }
QPushButton:disabled { color: #96a29c; background: #2a3b49; border-color: #566466; }
QMenu { background: #243747; color: #f4e7ca; border: 2px solid #c2a473; padding: 5px; }
QMenu::item { padding: 8px 24px 8px 12px; }
QMenu::item:selected { background: #486967; color: #ffe3ac; }
QMenu::separator { height: 1px; background: #6c807f; margin: 4px 8px; }
QScrollBar:vertical { width: 13px; background: #1b2b3c; }
QScrollBar::handle:vertical { background: #697d80; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #243747; color: #ffe3ac; border: 1px solid #c2a473; padding: 5px; }
"""


def panel(p, r, bright=False):
    p.fillRect(r,QColor('#233449' if not bright else '#3c5060'))
    for inset,color in ((0,'#172434'),(1,'#ddba83'),(2,'#f1d7a4'),(3,'#887657'),(4,'#293b50')):
        p.setPen(QPen(QColor(color),1))
        p.drawRect(r.adjusted(inset,inset,-inset-1,-inset-1))
    for x,y in ((r.left()+2,r.top()+2),(r.right()-3,r.top()+2),
                (r.left()+2,r.bottom()-3),(r.right()-3,r.bottom()-3)):
        p.fillRect(x,y,2,2,QColor('#fae2b1'))


def paint_overlay(game):
    p=QPainter(game)
    p.setRenderHint(QPainter.SmoothPixmapTransform,False)
    scene,_=game.desenhar_cena()
    p.drawImage(game.scene_rect,scene)
    # Text renders at screen resolution to preserve Portuguese and DPI readability.
    font=QFont('Segoe UI')
    font.setPixelSize(12)
    font.setWeight(QFont.DemiBold)
    p.setFont(font)
    title='ENSEADA DO POENTE · '+game._render.current_light.label
    p.setPen(QColor('#253647'))
    p.drawText(13,23,title)
    p.setPen(QColor('#f6dfb4'))
    p.drawText(12,22,title)
    info=f'{game.fmt_currency(game.estado["moedas"])} moedas'
    panel(p,QRect(12,game.H-30,146,23))
    p.fillRect(20,game.H-22,7,7,QColor('#c09554'))
    p.fillRect(22,game.H-22,3,5,QColor('#ffe5a1'))
    p.setPen(QColor('#f9e7bf'))
    p.drawText(QRect(32,game.H-29,119,21),Qt.AlignVCenter|Qt.AlignLeft,
               p.fontMetrics().elidedText(info,Qt.ElideRight,119))
    label='PAUSADO' if game.pausado else 'FISGADA!' if game.fisgando>0 else 'PESCANDO'
    w=p.fontMetrics().horizontalAdvance(label)+20
    panel(p,QRect(game.W-w-12,game.H-30,w,23))
    p.setPen(QColor('#f6d493' if game.pausado or game.fisgando>0 else '#c0d0bd'))
    p.drawText(QRect(game.W-w-12,game.H-29,w,21),Qt.AlignCenter,label)
    r=game.rect_icone
    panel(p,r,game.hover)
    for yy in (r.top()+9,r.top()+15,r.top()+21):
        p.fillRect(r.left()+9,yy,14,2,QColor('#ffe3ac' if game.hover else '#d7bb85'))
    if game.previa:
        p.setPen(QColor('#ffdfa1'))
        p.drawText(QRect(12,29,230,18),Qt.AlignLeft,'PRÉVIA DA LOJA')
    if game.popup:
        text,color,left=game.popup
        # Full-width wrap stays away from the fisherman and the menu.
        maxw=game.W-100
        bounds=p.fontMetrics().boundingRect(QRect(0,0,maxw-28,110),Qt.TextWordWrap,text)
        w=min(maxw,max(180,bounds.width()+28)); h=bounds.height()+26
        r=QRect((game.W-w)//2,39,w,h)
        p.setOpacity(min(1,left/.5))
        panel(p,r)
        p.setPen(QColor(color))
        p.drawText(r.adjusted(14,10,-14,-10),Qt.AlignCenter|Qt.TextWordWrap,text)
    p.end()
