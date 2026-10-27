"""Authored family silhouettes; finite shared cache, no gameplay RNG."""
from functools import lru_cache
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QPainter, QColor, QPolygon, QPen
from pesca_catalogo import ESPECIES


@lru_cache(maxsize=176)
def species_image(id_, unknown=False):
    s = ESPECIES[id_]; family = s['sprite']['family']; v = s['sprite']['variant']
    img = QImage(36,24,QImage.Format_ARGB32_Premultiplied); img.fill(Qt.transparent)
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing,False)
    def poly(points, color):
        p.setPen(Qt.NoPen);p.setBrush(QColor(color))
        p.drawPolygon(QPolygon([QPoint(x,y) for x,y in points]))
    def rect(x,y,w,h,c):p.fillRect(x,y,w,h,QColor(c))
    def line(a,b,c,width=1):p.setPen(QPen(QColor(c),width));p.drawLine(QPoint(*a),QPoint(*b))
    bases={'shark':'#738a98','whale':'#699eb6','orca':'#243747','dolphin':'#93b4be',
           'narwhal':'#aebebd','ray':'#6d829b','turtle':'#77a368','clownfish':'#ed973f',
           'parrot':'#4cc1cc','handfish':'#ce6d57','coelacanth':'#587aad',
           'squid':'#c98b8e','octopus':'#cb9075','jelly':'#e0adcd','shell':'#6c9aab',
           'crab':'#d47b4b','lobster':'#bb7160','shrimp':'#bd9d86','copepod':'#c3dbb6',
           'salp':'#a9d9d2','seahorse':'#d394aa','angler':'#7c6a86',
           'fang':'#809aa4','eel':'#66788e','lantern':'#7596ac','flatfish':'#af9671'}
    base=QColor(bases.get(family,'#7dafa3'))
    # Small palette and proportion variations identify species within a family.
    palette=s['sprite']['palette']
    base=QColor(*(max(20,min(240,ch+(sample%27)-13)) for ch,sample in zip((base.red(),base.green(),base.blue()),palette)))
    base=base.lighter(93+(v%7)*3); c=base.name(); dark=base.darker(160).name(); light=base.lighter(145).name()
    if family in ('whale','orca','dolphin','narwhal'):
        poly([(3,13),(7,8),(14,6),(23,8),(29,11),(30,14),(22,18),(10,18)],c)
        poly([(5,13),(0,8),(0,17)],dark);poly([(16,8),(19,3),(21,9)],dark)
        poly([(15,15),(22,15),(18,22)],dark);rect(23,10,2,2,'#162b3b')
        if family=='orca':poly([(19,12),(28,12),(25,17),(17,18)],'#f3f0dc');rect(23,9,3,1,'#f3f0dc')
        elif family=='narwhal':line((29,11),(35,5),'#f3e7b9');line((30,10),(34,8),'#d5c6a5')
        elif family=='dolphin':poly([(27,10),(34,12),(29,14)],c)
        else:line((27,15),(25,15),light);rect(20,8,5,1,light)
    elif family in ('ray','turtle'):
        if family=='ray':
            poly([(18,7),(7,3),(1,13),(8,15),(18,12),(28,16),(35,12),(28,3)],c)
            line((18,12),(15,23),dark);rect(16,7,1,1,light);rect(20,7,1,1,light)
        else:
            poly([(10,8),(5,4),(4,9),(8,13),(3,17),(7,20),(12,16)],dark)
            poly([(21,8),(29,4),(28,10),(24,13),(29,19),(24,21),(20,16)],dark)
            poly([(10,7),(21,6),(26,10),(24,16),(19,19),(11,17),(8,12)],c)
            rect(25,10,7,4,c);rect(30,11,1,1,'#24352d');line((12,9),(21,9),light)
            for x,y in ((13,12),(19,12),(16,16)):rect(x,y,3,2,dark)
    elif family in ('octopus','squid','jelly','salp'):
        poly([(12,4),(22,3),(26,7),(25,13),(10,13),(9,8)],c)
        for i in range(5):
            line((11+i*3,12),(10+i*4,19+i%2),light if i%2 else c)
            if family!='jelly':line((10+i*4,19+i%2),(8+i*4,21),c)
        if family=='squid':poly([(11,7),(18,0),(24,7)],light)
        if family=='salp':rect(13,6,9,6,'#d2efdf');rect(15,8,5,3,'#8bb7aa')
        if family!='jelly':rect(14,10,2,2,'#253446');rect(21,10,2,2,'#253446')
    elif family in ('crab','lobster','shrimp','copepod','shell'):
        if family=='shell':
            poly([(5,18),(7,8),(15,4),(23,5),(29,11),(28,18)],c)
            for x in (10,15,20,25):line((17,7),(x,17),light)
        else:
            poly([(10,8),(21,7),(27,12),(23,16),(12,17),(8,12)],c)
            for i in range(5):line((12+i*2,14),(8+i*4,21),dark)
            line((23,10),(32,4),light);line((23,11),(34,10),light)
            if family in ('crab','lobster'):
                for x in (3,28):rect(x,5,5,5,c);rect(x+1,4,2,2,light)
            if family=='copepod':line((11,9),(0,2),light);line((11,10),(1,19),light)
            rect(24,10,1,1,'#273341')
    elif family=='seahorse':
        poly([(18,3),(23,5),(26,7),(22,9),(20,9),(21,15),(18,19),(12,19),(10,16),(13,15),(14,17),(17,16),(15,10),(15,6)],c)
        rect(21,6,1,1,'#253247');line((15,9),(11,13),light);rect(18,3,2,2,light)
    else:
        long=family in ('eel','needle','fang','shark','long'); flat=family in ('flatfish','moonfish','disk')
        top=5 if flat else 10 if long else 8
        bottom=21 if flat else 15 if long else 18
        nose=30+v%3
        poly([(6,13),(10,top),(21,top-1),(28,top+2),(nose,12),(nose,15),(24,bottom),(12,bottom),(7,15)],c)
        poly([(7,13),(1,7+v%3),(1,20-v%3)],dark)
        poly([(12,top),(16,top-5-v%2),(22,top)],dark)
        poly([(16,bottom-2),(20,bottom+3),(22,bottom-2)],light)
        line((12,top+2),(24,top+2),light)
        rect(nose-5,11,2,2,'#1b2c3d');rect(nose-5,11,1,1,'#f7efd7')
        if family in ('catfish','eel'):line((nose-2,15),(35,18),light);line((nose-2,15),(34,21),light)
        if family in ('sailfish','flying'):poly([(11,top),(9,1),(20,2),(25,top)],light)
        if family=='angler':line((24,top),(24,2),light);line((24,2),(30,2),light);rect(29,2,3,3,'#ffeb94')
        if family in ('fang','angler'):rect(nose-4,15,4,1,'#f3edcc');rect(nose-3,14,1,3,'#f3edcc')
        if family=='clownfish':
            for x in (11,20,27):rect(x,top+2,2,bottom-top-3,'#f7e5c1')
        elif family=='lantern':
            for x in range(11,27,3):rect(x,bottom-2,1,1,'#e3fbb6')
        else:
            for x in range(10+(v%3),26,4+(v%3)):rect(x,top+4,1,2,dark)
        if family=='handfish':line((13,17),(10,21),c,2);line((22,17),(23,21),c,2)
    p.end()
    if unknown:
        p=QPainter(img);p.setCompositionMode(QPainter.CompositionMode_SourceIn)
        p.fillRect(img.rect(),QColor('#63717a'));p.end()
    return img
