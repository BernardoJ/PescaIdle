"""Platform presentation only; fishing rules remain shared."""
import os


def mobile():
    return os.getenv('PESCA_IDLE_MOBILE') == '1'


def fit_dialog(dialog):
    if not mobile():return dialog
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QScrollArea
    dialog.setWindowFlag(Qt.WindowStaysOnTopHint,False)
    dialog.setMinimumSize(0,0)
    content=QWidget();content.setLayout(QWidget.layout(dialog))
    scroll=QScrollArea();scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    outer=QVBoxLayout(dialog);outer.setContentsMargins(4,4,4,4);outer.addWidget(scroll)
    geo=QApplication.primaryScreen().availableGeometry()
    dialog.resize(geo.width(),geo.height())
    return dialog
