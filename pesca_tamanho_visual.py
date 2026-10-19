"""Per-instance painter transforms. Shared cached artwork is never changed."""
from functools import lru_cache
from PySide6.QtGui import QPainter, QColor
from pesca_especies_visual import species_image
from pesca_tamanhos import visual_scale, RULES, rule_snapshot

def scale_for(measurement,id_=None):
    if not measurement:return 1.
    rule=measurement.get('visual_rule') or (rule_snapshot(id_) if id_ in RULES else measurement['rule'])
    return visual_scale(measurement['mm'],rule)

@lru_cache(maxsize=176)
def capture_outline(id_):
    image=species_image(id_).copy()
    ink=QPainter(image)
    ink.setCompositionMode(QPainter.CompositionMode_SourceIn)
    ink.fillRect(image.rect(),QColor('#172b3b'))
    ink.end()
    return image


def draw_fish(painter,id_,x,y,measurement=None,reverse=False,base_scale=1.,contrast=False):
    s=scale_for(measurement,id_)*base_scale
    if contrast:
        # One logical pixel of contrast in the capture scene, outside the body.
        # The original art and its uniform scale are untouched; tank stays as-is.
        for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
            painter.save()
            painter.setRenderHint(QPainter.SmoothPixmapTransform,False)
            painter.translate(x+dx,y+dy);painter.scale(-s if reverse else s,s)
            painter.drawImage(-18,-12,capture_outline(id_))
            painter.restore()
    painter.save()
    painter.setRenderHint(QPainter.SmoothPixmapTransform,False)
    painter.translate(x,y);painter.scale(-s if reverse else s,s)
    painter.drawImage(-18,-12,species_image(id_))
    painter.restore()
    return 36*s,24*s
