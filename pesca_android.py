"""Android bootstrap, private profile and suspend/resume integration."""
import os
from pathlib import Path
from PySide6.QtCore import Qt,QStandardPaths
from PySide6.QtWidgets import QApplication


class MobileLifecycle:
    def __init__(self,app,game):
        self.game=game;self.suspended=False
        app.applicationStateChanged.connect(self.changed)

    def changed(self,state):
        g=self.game
        if state!=Qt.ApplicationActive:
            if not self.suspended:
                g.tick();g.salvar()
                g.relogio.stop();g.timer_save.stop();self.suspended=True
        elif self.suspended:
            report=g.simular_offline()
            if report:g.mostrar_popup(report,'#ffe3ac')
            g._sync_fishing();g.ultimo_tick=g._monotonic();g._ultimo_civil=g._wall()
            g.relogio.start(66);g.timer_save.start(30000);self.suspended=False


def run():
    os.environ['PESCA_IDLE_MOBILE']='1'
    app=QApplication.instance() or QApplication([])
    app.setApplicationName('PescaIdle');app.setOrganizationName('BernardoJ')
    if not os.getenv('PESCA_IDLE_SAVE_PATH'):
        root=QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not root:raise RuntimeError('Diretório privado do aplicativo indisponível.')
        os.environ['PESCA_IDLE_SAVE_PATH']=str(Path(root)/'save.json')
    # The profile override is established before any game import.
    from pesca_ui import configure_app
    from pesca_idle import JogoPesca
    configure_app(app)
    game=JogoPesca();lifecycle=MobileLifecycle(app,game)
    game.showMaximized()
    return app.exec()
