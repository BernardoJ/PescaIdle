"""Original pixel geometry for all eleven rod tiers and the underwater bait."""
import math
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QPolygon

ROD_RAMPS=(('#725644','#c1a574','#f0d39a'),('#63704d','#aeb984','#dae1a3'),
           ('#704a42','#c08363','#efb984'),('#395567','#7397a8','#c4d4ce'),
           ('#764743','#ba6a56','#f2b382'),('#534d69','#9987b7','#dccbe0'),
           ('#2c646b','#67b9b6','#b9e6d4'),('#654674','#b47da2','#e9b8d8'),
           ('#395386','#789ecc','#c4daed'),('#796345','#c8a16b','#ffe0a0'),
           ('#57527e','#afa8d8','#f2dfb1'))


def segment(p,a,b,color,width=1):
    p.setPen(QPen(QColor(color),width,Qt.SolidLine,Qt.SquareCap,Qt.MiterJoin))
    p.drawLine(QPoint(*a),QPoint(*b))


def rod(p,hand,tip,level,f,pose):
    shadow,mid,highlight=ROD_RAMPS[min(max(0,level),10)]
    hx,hy=hand;tx,ty=tip
    bend=2 if pose==1 else 1
    points=[hand,(round(hx+(tx-hx)*.42),round(hy+(ty-hy)*.42)+bend),
            (round(hx+(tx-hx)*.77),round(hy+(ty-hy)*.77)+bend),tip]
    for a,b in zip(points,points[1:]):
        segment(p,(a[0],a[1]+1),(b[0],b[1]+1),shadow,2)
        segment(p,a,b,mid)
        segment(p,(a[0],a[1]-1),(b[0],b[1]-1),highlight)
    butt=(hx-6,hy+3)
    segment(p,butt,hand,'#483b39',3)
    segment(p,(butt[0],butt[1]-1),(hx-1,hy-1),'#bd9770')
    for i in range(3):p.fillRect(hx-5+i*2,hy+2-i,1,2,QColor('#76503b'))
    # Brass reel, central spindle and small crank, attached below the hand.
    p.setPen(Qt.NoPen);p.setBrush(QColor('#4b484b'))
    p.drawPolygon(QPolygon([QPoint(hx+1,hy+2),QPoint(hx+4,hy+1),QPoint(hx+6,hy+3),
                            QPoint(hx+5,hy+6),QPoint(hx+2,hy+6)]))
    p.fillRect(hx+2,hy+2,3,3,QColor('#b58b59'))
    p.fillRect(hx+3,hy+2,1,2,QColor('#f0d39a'))
    p.fillRect(hx+6,hy+4,2,1,QColor('#596570'))
    p.fillRect(hx+7,hy+3,1,2,QColor('#d7c29b'))
    for t in (.27,.55,.81):
        x=round(hx+(tx-hx)*t);y=round(hy+(ty-hy)*t)+bend
        p.fillRect(x,y-1,2,3,QColor('#91744f' if level<4 else '#bdc9ce'))
        p.fillRect(x+1,y-1,1,1,QColor(highlight))
    if level>=6:
        p.fillRect(hx+3,hy+3,1,1,QColor('#b6e7d8'))
    if level>=9:
        p.fillRect(hx+10,hy-5,2,2,QColor('#efd395'))


def bait(p,x,y,f):
    p.save();p.setOpacity(.55)
    bx=x+round(math.sin(f*2.4)*2);by=y+13+round(math.sin(f*1.7))
    segment(p,(x,y+3),(bx,by),'#8cb3b1')
    segment(p,(bx,by),(bx,by+3),'#b9c2b3')
    segment(p,(bx,by+3),(bx+2,by+4),'#b9c2b3')
    segment(p,(bx+2,by+4),(bx+3,by+2),'#b9c2b3')
    for dx,dy,color in ((0,0,'#bd7b69'),(1,1,'#daaf8a'),(0,2,'#cb9275'),
                         (-1,3,'#a66d64'),(0,4,'#c39078')):
        p.fillRect(bx+dx,by+dy,2,1,QColor(color))
    p.restore()
