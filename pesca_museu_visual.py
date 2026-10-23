"""Original aquarium-only pixel artwork. No random draws or persistent state.

72x48 masters retain the existing 36x24 logical footprint. At one physical
pixel per logical pixel, small details are omitted before nearest sampling.
The catalogue contains explicit geometry/marks, not a hash-based recolouring.
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPolygon
from pesca_tamanho_visual import scale_for

ASSETS = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets'
ART = json.loads((ASSETS / 'aquario_especies.json').read_text(encoding='utf-8'))


def _polygon(points):
    return QPolygon([QPoint(x, y) for x, y in points])


def _primitive(painter, item):
    kind, color, values = item
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


@lru_cache(maxsize=136)
def aquarium_species_image(species_id, detail=2):
    """Treat the returned cache as read-only, just like species_image."""
    if detail not in (1, 2):
        raise ValueError('Aquarium detail must be 1 or 2.')
    profile = ART['species'][species_id]  # Never silently substitute another fish.
    image = QImage(72, 48, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, False)
    for item in profile['back']:
        _primitive(painter, item)
    if detail == 2:
        for item in profile['back_fine']:
            _primitive(painter, item)
    painter.setPen(QColor(profile['outline']))
    painter.setBrush(QColor(profile['body_color']))
    painter.drawPolygon(_polygon(profile['body']))
    path = QPainterPath()
    path.addPolygon(_polygon(profile['body']))
    painter.save()
    painter.setClipPath(path)
    for item in profile['marks']:
        _primitive(painter, item)
    if detail == 2:
        for item in profile['fine']:
            _primitive(painter, item)
    painter.restore()
    # A final one-pixel contour contains patterns and separates dark fish from water.
    painter.setPen(QColor(profile['outline']))
    painter.setBrush(Qt.NoBrush)
    painter.drawPolygon(_polygon(profile['body']))
    for item in profile['front']:
        _primitive(painter, item)
    painter.end()
    if detail == 1:
        image = image.scaled(36, 24, Qt.IgnoreAspectRatio, Qt.FastTransformation)
    # Authored coordinates face left. The tank's existing direction convention
    # expects a right-facing master (reverse=True accompanies leftward travel).
    return image.mirrored(True, False)


def draw_aquarium_fish(painter, species_id, x, y, measurement=None,
                       reverse=False, detail=1):
    """Uniform transform; specimen scale, slots and swim bounds stay unchanged."""
    scale = scale_for(measurement, species_id)
    painter.save()
    painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
    painter.translate(x, y)
    painter.scale(-scale if reverse else scale, scale)
    painter.drawImage(QRectF(-18, -12, 36, 24),
                      aquarium_species_image(species_id, detail))
    painter.restore()
    return 36 * scale, 24 * scale
