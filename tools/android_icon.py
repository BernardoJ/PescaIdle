"""Original pixel launcher icon, built from code in the game's palette."""
from PySide6.QtCore import Qt,QPoint
from PySide6.QtGui import QImage,QPainter,QColor,QPolygon


def make(path):
    image=QImage(32,32,QImage.Format_ARGB32);image.fill(QColor('#172838'))
    p=QPainter(image);p.setPen(Qt.NoPen)
    def rect(x,y,w,h,color):p.fillRect(x,y,w,h,QColor(color))
    rect(2,2,28,28,'#253c50');rect(3,3,26,16,'#345266')
    rect(22,5,5,5,'#efc581');rect(23,4,3,7,'#efc581')
    rect(4,17,24,12,'#27627b')
    for x,y in ((5,19),(22,20),(4,26),(20,27)):rect(x,y,7,1,'#58a9b3')
    p.setBrush(QColor('#a05c39'));p.drawPolygon(QPolygon([QPoint(6,20),QPoint(27,20),QPoint(23,25),QPoint(10,25)]))
    rect(7,20,19,2,'#e0a45c');rect(11,24,11,1,'#704036')
    rect(12,15,4,5,'#a65245');rect(12,12,3,3,'#d49b67')
    rect(10,11,8,2,'#efc581');rect(12,9,4,2,'#bd8952')
    p.setPen(QColor('#efc581'));p.drawLine(15,16,26,12);p.drawLine(26,12,26,22)
    rect(25,22,3,2,'#d05d57');rect(1,1,30,1,'#efc581');rect(1,30,30,1,'#efc581')
    p.end()
    if not image.scaled(256,256,Qt.IgnoreAspectRatio,Qt.FastTransformation).save(str(path),'PNG'):
        raise RuntimeError('Launcher icon write failed')
