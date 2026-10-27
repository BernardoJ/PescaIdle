"""Original aquarium-only pixel artwork. No random draws or persistent state.

72x48 masters retain the existing 36x24 logical footprint. At one physical
pixel per logical pixel, small details are omitted before nearest sampling.
The catalogue contains explicit geometry/marks, not a hash-based recolouring.
"""
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPolygon
from pesca_tamanho_visual import scale_for

ASSETS = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets'
ART = json.loads((ASSETS / 'aquario_especies.json').read_text(encoding='utf-8'))
MOTION = json.loads((ASSETS / 'aquario_movimento.json').read_text(encoding='utf-8'))
WAVE = (0., .7, 1., .7, 0., -.7, -1., -.7)


def animation_frame(species_id, phase):
    """Visual seconds only: independent of game time, state and all RNGs."""
    if not math.isfinite(phase):
        raise ValueError('Aquarium phase must be finite.')
    return math.floor(phase / MOTION['species'][species_id]['step_seconds']) % len(WAVE)


def _tail_warp(anchor, wave, undulate=False):
    def warp(x, y):
        lever = max(0., min(1., (x-anchor)/(70-anchor)))
        if undulate:
            return x, y + round(2*lever*wave)
        # Small projected caudal stroke, anchored at the peduncle. Never scale
        # the whole fish: the head/body and specimen length rule stay intact.
        return x-round(2*lever*abs(wave)), y+round(lever*wave)
    return warp


def _fin_warp(item, wave):
    anchor_x, anchor_y = item[2][0]
    def warp(x, y):
        lever = min(1., math.hypot(x-anchor_x,y-anchor_y)/10)
        return x+round(lever*wave), y+round(lever*wave)
    return warp


def _polygon(points):
    return QPolygon([QPoint(x, y) for x, y in points])


def _primitive(painter, item, warp=None):
    kind, color, values = item
    if warp is not None:
        if kind in ('poly','line'):
            values = [warp(x,y) for x,y in values]
        else:
            x,y,w,h = values
            cx,cy = warp(x+w//2,y+h//2)
            values = [x+cx-(x+w//2),y+cy-(y+h//2),w,h]
    painter.setPen(QColor(color))
    painter.setBrush(QColor(color))
    if kind == 'poly':
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(_polygon(values))
    elif kind == 'line':
        painter.drawPolyline(_polygon(values))
    elif kind == 'rect':
        painter.fillRect(*values, QColor(color))
    elif kind == 'ellipse':
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(*values)
    else:
        raise ValueError('Aquarium artwork: unknown primitive ' + kind)


def _paint_species(painter, species_id, detail, frame):
    """Same paint path for cached masters and padded geometry verification."""
    profile = ART['species'][species_id]
    motion = MOTION['species'][species_id]
    wave = WAVE[frame]
    tail = _tail_warp(motion['anchor_x'],wave,motion['style']=='undulate')
    body_warp = tail if motion['style']=='undulate' else None
    body = [body_warp(x,y) for x,y in profile['body']] if body_warp else profile['body']
    painter.setRenderHint(QPainter.Antialiasing, False)
    for index,item in enumerate(profile['back']):
        warp = body_warp
        if index in motion['tail_back']:
            warp = tail
        elif index in motion['fins_back']:
            warp = _fin_warp(item,wave)
        _primitive(painter, item,warp)
    if detail == 2:
        for item in profile['back_fine']:
            _primitive(painter, item,tail if motion['tail_back'] else body_warp)
    painter.setPen(QColor(profile['outline']))
    painter.setBrush(QColor(profile['body_color']))
    painter.drawPolygon(_polygon(body))
    path = QPainterPath()
    path.addPolygon(_polygon(body))
    painter.save()
    painter.setClipPath(path)
    for item in profile['marks']:
        _primitive(painter, item,body_warp)
    if detail == 2:
        for item in profile['fine']:
            _primitive(painter, item,body_warp)
    painter.restore()
    # A final one-pixel contour contains patterns and separates dark fish from water.
    painter.setPen(QColor(profile['outline']))
    painter.setBrush(Qt.NoBrush)
    painter.drawPolygon(_polygon(body))
    for index,item in enumerate(profile['front']):
        warp = _fin_warp(item,-wave) if index in motion['fins_front'] else body_warp
        _primitive(painter, item,warp)


@lru_cache(maxsize=512, typed=True)
def aquarium_species_image(species_id, detail=2, frame=0):
    """Read-only cache: at most 512 small frames, not one image per clock tick."""
    if detail not in (1, 2):
        raise ValueError('Aquarium detail must be 1 or 2.')
    if type(frame) is not int or not 0 <= frame < len(WAVE):
        raise ValueError('Aquarium frame must be an integer from 0 to 7.')
    image = QImage(72, 48, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    _paint_species(painter,species_id,detail,frame)
    painter.end()
    if detail == 1:
        image = image.scaled(36, 24, Qt.IgnoreAspectRatio, Qt.FastTransformation)
    # Authored coordinates face left. The tank's existing direction convention
    # expects a right-facing master (reverse=True accompanies leftward travel).
    return image.mirrored(True, False)


def draw_aquarium_fish(painter, species_id, x, y, measurement=None,
                       reverse=False, detail=1, phase=0.):
    """Uniform transform; specimen scale, slots and swim bounds stay unchanged."""
    scale = scale_for(measurement, species_id)
    painter.save()
    painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
    painter.translate(x, y)
    painter.scale(-scale if reverse else scale, scale)
    painter.drawImage(QRectF(-18, -12, 36, 24),
                      aquarium_species_image(species_id,detail,animation_frame(species_id,phase)))
    painter.restore()
    return 36 * scale, 24 * scale
