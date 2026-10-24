"""Hard boundary for this disposable candidate's profiles; never use APPDATA saves."""
import os
import sys
from pathlib import Path

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent

def validate_profile_path(path):
    target = Path(path).expanduser().resolve()
    if not target.is_relative_to(ROOT) or target == ROOT:
        raise ValueError('Piloto isolado: o perfil deve ficar dentro da pasta deste candidato.')
    return target

def prepare_profile():
    target = validate_profile_path(os.environ.get('PESCA_IDLE_SAVE_PATH', ROOT/'perfil-piloto'/'save.json'))
    os.environ['PESCA_IDLE_SAVE_PATH'] = str(target)
    return target
