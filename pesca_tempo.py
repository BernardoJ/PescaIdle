"""One civil-clock contract for fishing, UI and lighting; no Qt dependency."""
from datetime import datetime, timedelta, timezone

PERIODOS = (
    ('amanhecer', 'Amanhecer', 5, 7), ('manha', 'Manhã', 7, 9),
    ('dia', 'Dia', 9, 11), ('meio_dia', 'Meio-dia', 11, 14),
    ('tarde', 'Tarde', 14, 17), ('anoitecer', 'Anoitecer', 17, 20),
    ('noite', 'Noite', 20, 5),
)
LABELS = {p[0]: p[1] for p in PERIODOS}


def periodo(moment):
    hour = moment.hour
    return next(id_ for id_, _, start, end in PERIODOS
                if (start <= hour < end if start < end else hour >= start or hour < end))


def proxima_mudanca(moment):
    boundaries = [moment.replace(hour=p[2], minute=0, second=0, microsecond=0)
                  for p in PERIODOS]
    return min(t if t > moment else t + timedelta(days=1) for t in boundaries)


def snapshot(timestamp=None, offset_seconds=None):
    utc = datetime.now(timezone.utc) if timestamp is None else datetime.fromtimestamp(timestamp, timezone.utc)
    local = utc.astimezone() if offset_seconds is None else utc.astimezone(timezone(timedelta(seconds=offset_seconds)))
    return {'utc': utc.timestamp(), 'offset_seconds': int(local.utcoffset().total_seconds()),
            'local_iso': local.isoformat(), 'periodo_id': periodo(local),
            'rotulo': LABELS[periodo(local)],
            'proxima_utc': proxima_mudanca(local).timestamp()}
