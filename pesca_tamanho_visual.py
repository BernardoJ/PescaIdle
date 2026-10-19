"""Per-instance painter transforms. Shared cached artwork is never changed."""
from PySide6.QtGui import QPainter
from pesca_especies_visual import species_image
from pesca_tamanhos import visual_scale, RULES, rule_snapshot

def scale_for(measurement,id_=None):
    if not measurement:return 1.
    rule=measurement.get('visual_rule') or (rule_snapshot(id_) if id_ in RULES else measurement['rule'])
    return visual_scale(measurement['mm'],rule)

def draw_fish(painter,id_,x,y,measurement=None,reverse=False,base_scale=1.):
    s=scale_for(measurement,id_)*base_scale
    painter.save()
    painter.setRenderHint(QPainter.SmoothPixmapTransform,False)
    painter.translate(x,y);painter.scale(-s if reverse else s,s)
    painter.drawImage(-18,-12,species_image(id_))
    painter.restore()
    return 36*s,24*s
