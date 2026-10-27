"""Android bootstrap, private profile and suspend/resume integration."""
import os
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QMessageBox


class MobileLifecycle:
    def __init__(self,app,game):
        self.game=game;self.suspended=False
        app.applicationStateChanged.connect(self.changed)

    def changed(self,state):
        g=self.game
        if g._closed:return
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
    qa=os.getenv('PESCA_IDLE_ANDROID_QA')=='1'
    from pesca_piloto import prepare_android_profile
    try:
        prepare_android_profile(qa=qa)
    except (OSError, ValueError) as exc:
        QMessageBox.critical(None,'Não foi possível abrir o perfil',str(exc))
        return 1
    # The profile override is established before any game import.
    from pesca_ui import configure_app
    from pesca_idle import JogoPesca,ESTADO_PADRAO
    from pesca_save import SaveError
    configure_app(app)
    reopen_snapshot=None
    if qa:
        from tools.android_smoke import read_reopen_snapshot
        reopen_snapshot=read_reopen_snapshot(ESTADO_PADRAO)
    try:game=JogoPesca()
    except SaveError as exc:
        QMessageBox.critical(None,'Não foi possível abrir o perfil',str(exc))
        return 1
    lifecycle=MobileLifecycle(app,game)
    game.showMaximized()
    game.windowHandle().safeAreaMarginsChanged.connect(game._fit_mobile_viewport)
    game._fit_mobile_viewport()
    if qa:
        from tools.android_smoke import schedule
        schedule(app,game,lifecycle,reopen_snapshot)
    return app.exec()
