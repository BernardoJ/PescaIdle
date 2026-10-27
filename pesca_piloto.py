"""Profile boundaries for the desktop pilot and Android's private pilot context."""
import os
import sys
from pathlib import Path

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
PILOT_KIND = 'tamanhos-v1'
_android_root = None


def validate_profile_path(path):
    target = Path(path).expanduser().resolve()
    boundary = _android_root if _android_root is not None else ROOT
    if not target.is_relative_to(boundary) or target == boundary:
        raise ValueError('Piloto isolado: o perfil deve ficar dentro da pasta deste contexto.')
    return target


def prepare_profile():
    default = (_android_root/'save.json' if _android_root is not None
               else ROOT/'perfil-piloto'/'save.json')
    target = validate_profile_path(os.environ.get('PESCA_IDLE_SAVE_PATH', default))
    os.environ['PESCA_IDLE_SAVE_PATH'] = str(target)
    return target


def prepare_android_profile(qa=False):
    """Select a private boundary before game imports; never trust an env root.

    QStandardPaths belongs to the running application/package. The production
    pilot gets a dedicated directory; the separate QA package gets a cache
    context that persists across process restarts. Legacy saves at AppDataLocation/save.json are intentionally untouched.
    """
    from PySide6.QtCore import QStandardPaths
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None or app.platformName() != 'android':
        raise ValueError('O perfil Android requer o bootstrap Qt Android nativo.')
    location = QStandardPaths.CacheLocation if qa else QStandardPaths.AppDataLocation
    value = QStandardPaths.writableLocation(location)
    if not value or not Path(value).is_absolute():
        raise ValueError('Diretório privado do aplicativo indisponível.')
    private = Path(value).resolve()
    if qa and 'br.com.bernardoj.pescaidle.qa' not in private.parts:
        raise ValueError('O contexto QA requer o pacote Android descartável separado.')
    boundary = private/'qa-tamanhos-v1' if qa else private/'pilotos'/PILOT_KIND
    # Do not follow a preexisting pilot-directory alias into a legacy/other context.
    if boundary.resolve() != boundary:
        raise ValueError('Diretório privado do piloto redirecionado; original preservado.')
    target = boundary/'save.json'
    override = os.environ.get('PESCA_IDLE_SAVE_PATH')
    if override:
        target = Path(override).expanduser().resolve()
    if target == boundary or not target.is_relative_to(boundary):
        raise ValueError('Piloto Android isolado: perfil fora deste contexto privado.')
    boundary.mkdir(parents=True, exist_ok=True)
    global _android_root
    _android_root = boundary
    os.environ['PESCA_IDLE_SAVE_PATH'] = str(target)
    if qa:
        os.environ['PESCA_IDLE_QA_DIR'] = str(boundary)
    return target
