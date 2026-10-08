"""Platform presentation only; fishing rules remain shared."""
import os


def mobile():
    return os.getenv('PESCA_IDLE_MOBILE') == '1'


def safe_rect(widget):
    rect=widget.rect()
    handle=widget.windowHandle()
    if mobile() and handle is not None:
        rect=rect.marginsRemoved(handle.safeAreaMargins())
    return rect


def fit_dialog(dialog):
    if not mobile():return dialog
    from PySide6.QtCore import Qt,QTimer
    from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QScrollArea,QLabel,QComboBox,QSizePolicy,QScroller
    dialog.setWindowFlag(Qt.WindowStaysOnTopHint,False)
    dialog.setMinimumSize(0,0)
    content=QWidget();content.setLayout(QWidget.layout(dialog))
    for label in content.findChildren(QLabel):
        label.setWordWrap(True)
        label.setMinimumWidth(0)
        label.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
    for combo in content.findChildren(QComboBox):
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(12)
    scroll=QScrollArea();scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    outer=QVBoxLayout(dialog);outer.setContentsMargins(4,4,4,4);outer.addWidget(scroll)
    QScroller.grabGesture(scroll.viewport(),QScroller.TouchGesture)
    def insets(*_):
        handle=dialog.windowHandle()
        if handle is not None:
            margins=handle.safeAreaMargins()
            outer.setContentsMargins(margins.left()+4,margins.top()+4,margins.right()+4,margins.bottom()+4)
            if not getattr(dialog,'_safe_connected',False):
                handle.safeAreaMarginsChanged.connect(insets);dialog._safe_connected=True
    QTimer.singleShot(0,insets)
    geo=QApplication.primaryScreen().availableGeometry()
    dialog.resize(geo.width(),geo.height())
    return dialog
