"""Android bootstrap, private profile and suspend/resume integration."""
import os
import uuid
from pathlib import Path
from PySide6.QtCore import Qt,QStandardPaths
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
    if qa:
        # Only the separate QA package sets this flag. Establish its disposable
        # profile before importing any game module; production profiles stay out.
        root=Path(QStandardPaths.writableLocation(QStandardPaths.CacheLocation))/('qa-'+uuid.uuid4().hex)
        root.mkdir(parents=True)
        os.environ['PESCA_IDLE_SAVE_PATH']=str(root/'save.json')
        os.environ['PESCA_IDLE_QA_DIR']=str(root)
    if not os.getenv('PESCA_IDLE_SAVE_PATH'):
        root=QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not root:raise RuntimeError('Diretório privado do aplicativo indisponível.')
        os.environ['PESCA_IDLE_SAVE_PATH']=str(Path(root)/'save.json')
    # The profile override is established before any game import.
    from pesca_ui import configure_app
    from pesca_idle import JogoPesca
    from pesca_save import SaveError
    configure_app(app)
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
        schedule(app,game,lifecycle)
    return app.exec()
