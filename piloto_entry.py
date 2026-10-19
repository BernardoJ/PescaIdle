"""Standalone candidate entry; smoke mode requires explicit isolated paths."""
import os
import sys
from pesca_piloto import validate_profile_path

if '--pilot-smoke' in sys.argv:
    for key in ('PESCA_IDLE_SAVE_PATH','PESCA_IDLE_PILOT_QA_DIR'):
        if not os.environ.get(key):raise RuntimeError('Smoke do piloto exige '+key)
        validate_profile_path(os.environ[key])

if __name__=='__main__':
    if '--demo' in sys.argv:
        from tools.demo_tamanhos import run
        sys.exit(run())
    if '--pilot-smoke' in sys.argv:
        from tools.pilot_smoke import run
        sys.exit(run())
    from pesca_idle import main
    from tools.dev_access import DevAccess
    main(DevAccess())
