"""Interactive local demo with disposable synthetic discoveries only."""
import argparse
import os
from pathlib import Path
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description='Prévia local isolada do museu.')
    parser.add_argument('--empty',action='store_true',help='Começar sem descobertas.')
    parser.add_argument('--auto-close-ms',type=int,default=0,help=argparse.SUPPRESS)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='pesca-museum-preview-') as tmp:
        # Establish all persistence paths before Qt/game imports.
        os.environ.update(PESCA_IDLE_SAVE_PATH=str(Path(tmp)/'save.json'),
                          APPDATA=str(Path(tmp)/'appdata'),LOCALAPPDATA=str(Path(tmp)/'localappdata'))
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        from PySide6.QtWidgets import QApplication
        from pesca_ui import configure_app
        from pesca_idle import JogoPesca
        from pesca_museu import change_exhibit
        from pesca_museu_ui import MuseuDialog
        app=QApplication([]);configure_app(app)
        game=JogoPesca();game.pausado=True;game.estado['pausado']=True
        if not args.empty:
            ids=('lambari','peixe_palhaco','cirurgiao_patela')
            game.estado['inventario_por_id']={id_:1 for id_ in ids}
            game.estado['total_pescados']=3
            for slot,id_ in enumerate(ids):
                game.estado=change_exhibit(game.estado,slot,id_)
        if not game.salvar():
            raise RuntimeError(game._save_error)
        dialog=MuseuDialog(game)
        dialog.setWindowTitle('Prévia local — descobertas de exemplo, perfil descartável')
        dialog.finished.connect(game.close)
        dialog.show()
        if args.auto_close_ms:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(max(1,args.auto_close_ms),dialog.accept)
        try:
            return app.exec()
        finally:
            game.close()


if __name__=='__main__':
    sys.exit(main())
